from flask import render_template, request, redirect, url_for, flash, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import json
from datetime import datetime

from app.web import web_bp
from app.extensions import db
from app.models import User, Fund, Note, Purchase, FundValue
from app.services.fund_value_service import get_fund_values_by_date_range, fetch_fund_value, calculate_fund_performance
from app.services.fund_service import fetch_fund_details

# 辅助函数
def get_fund(fund_id):
    """根据ID获取基金信息"""
    return Fund.query.get(fund_id)

# Home page
@web_bp.route('/')
def index():
    """首页"""
    # 获取最新的笔记
    recent_notes = Note.query.filter_by(is_public=True).order_by(Note.created_at.desc()).limit(5).all()
    
    # 获取热门基金
    popular_funds = Fund.query.join(Note).group_by(Fund.id).order_by(db.func.count(Note.id).desc()).limit(5).all()
    
    return render_template('index.html', recent_notes=recent_notes, popular_funds=popular_funds)

# Fund pages
@web_bp.route('/funds')
def funds():
    """基金列表页"""
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    fund_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # 构建查询
    query = Fund.query
    
    # 如果有关键字，则搜索基金代码或名称
    if keyword:
        query = query.filter(
            (Fund.code.like(f'%{keyword}%')) | 
            (Fund.name.like(f'%{keyword}%'))
        )
    
    # 如果指定了基金类型，则过滤
    if fund_type:
        query = query.filter_by(type=fund_type)
    
    # 按基金代码排序
    query = query.order_by(Fund.code)
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    funds = pagination.items
    
    # 获取所有基金类型
    fund_types = db.session.query(Fund.type).distinct().all()
    fund_types = [t[0] for t in fund_types if t[0]]
    
    return render_template('funds.html', 
                          funds=funds, 
                          pagination=pagination, 
                          keyword=keyword, 
                          fund_type=fund_type,
                          fund_types=fund_types)

@web_bp.route('/funds/<string:code>')
def fund_detail(code):
    """基金详情页"""
    # 查询基金
    fund = Fund.query.filter_by(code=code).first_or_404()
    
    # 如果基金信息不完整，尝试从API获取详细信息
    if not fund.company or not fund.manager or not fund.inception_date or fund.size is None:
        updated_fund = fetch_fund_details(code)
        if updated_fund:
            fund = updated_fund
    
    # 获取基金相关笔记
    page = request.args.get('page', 1, type=int)
    per_page = 10
    notes_query = Note.query.filter_by(fund_id=fund.id, is_public=True).order_by(Note.created_at.desc())
    notes_pagination = notes_query.paginate(page=page, per_page=per_page)
    notes = notes_pagination.items
    
    # 获取基金净值数据（最多100条最近记录）
    fund_values = FundValue.query.filter_by(fund_id=fund.id)\
        .order_by(FundValue.date.asc())\
        .limit(100).all()
    
    # 如果没有净值数据且用户已登录，尝试获取
    if not fund_values and current_user.is_authenticated:
        try:
            fetch_fund_value(fund_code=code)
            # 重新查询
            fund_values = FundValue.query.filter_by(fund_id=fund.id)\
                .order_by(FundValue.date.asc())\
                .limit(100).all()
        except Exception as e:
            flash(f'获取基金净值数据失败: {str(e)}', 'danger')
    
    # 如果用户已登录，获取用户对该基金的购买记录
    user_purchases = []
    if current_user.is_authenticated:
        user_purchases = Purchase.query.filter_by(
            user_id=current_user.id,
            fund_id=fund.id
        ).order_by(Purchase.purchase_date.asc()).all()
    
    return render_template('fund_detail.html', 
                          fund=fund, 
                          notes=notes, 
                          pagination=notes_pagination,
                          fund_values=fund_values,
                          user_purchases=user_purchases)

# Note pages
@web_bp.route('/notes')
def notes():
    """笔记列表页"""
    # 获取查询参数
    fund_id = request.args.get('fund_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 构建查询
    query = Note.query.filter_by(is_public=True)
    
    # 如果指定了基金ID，则过滤
    if fund_id:
        query = query.filter_by(fund_id=fund_id)
    
    # 按创建时间降序排序
    query = query.order_by(Note.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    notes = pagination.items
    
    return render_template('notes.html', notes=notes, pagination=pagination, fund_id=fund_id)

@web_bp.route('/notes/<int:note_id>')
def note_detail(note_id):
    """笔记详情页"""
    note = Note.query.get_or_404(note_id)
    
    # 检查笔记是否公开
    if not note.is_public and (not current_user.is_authenticated or current_user.id != note.user_id):
        abort(403)
    
    # 获取相关信息
    fund = Fund.query.get(note.fund_id)
    author = User.query.get(note.user_id)
    
    # 获取同一基金的其他笔记
    related_notes = Note.query.filter(Note.fund_id == note.fund_id, 
                                     Note.id != note.id,
                                     Note.is_public == True).order_by(Note.created_at.desc()).limit(5).all()
    
    return render_template('note_detail.html', 
                          note=note, 
                          fund=fund, 
                          author=author, 
                          related_notes=related_notes)

# Auth pages
@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.verify_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('登录成功！', 'success')
            return redirect(next_page or url_for('web.index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('请填写所有必填字段', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已存在', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.password = password
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('注册成功！', 'success')
        return redirect(url_for('web.index'))
    
    return render_template('register.html')

@web_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('web.index'))

# User profile
@web_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """用户个人资料页"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        avatar = request.form.get('avatar')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 更新用户名
        if username and username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('用户名已存在', 'danger')
                return render_template('profile.html')
            current_user.username = username
        
        # 更新邮箱
        if email and email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('邮箱已存在', 'danger')
                return render_template('profile.html')
            current_user.email = email
        
        # 更新头像
        if avatar:
            current_user.avatar = avatar
        
        # 更新密码
        if current_password and new_password:
            if not current_user.verify_password(current_password):
                flash('当前密码错误', 'danger')
                return render_template('profile.html')
            
            if new_password != confirm_password:
                flash('两次输入的新密码不一致', 'danger')
                return render_template('profile.html')
            
            current_user.password = new_password
        
        db.session.commit()
        flash('个人资料已更新', 'success')
        return redirect(url_for('web.profile'))
    
    return render_template('profile.html')

@web_bp.route('/my-notes')
@login_required
def my_notes():
    """我的笔记页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取用户的笔记
    query = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page)
    notes = pagination.items
    
    return render_template('my_notes.html', notes=notes, pagination=pagination)

# Note management
@web_bp.route('/notes/create', methods=['GET', 'POST'])
@login_required
def create_note():
    """创建笔记页面"""
    if request.method == 'POST':
        fund_id = request.form.get('fund_id', type=int)
        title = request.form.get('title')
        content = request.form.get('content')
        rating = request.form.get('rating', type=int)
        is_public = request.form.get('is_public') == 'on'
        
        if not fund_id or not title or not content:
            flash('请填写所有必填字段', 'danger')
            funds = Fund.query.order_by(Fund.code).all()
            return render_template('create_note.html', funds=funds)
        
        # 检查基金是否存在
        fund = Fund.query.get(fund_id)
        if not fund:
            flash('所选基金不存在', 'danger')
            funds = Fund.query.order_by(Fund.code).all()
            return render_template('create_note.html', funds=funds)
        
        # 创建笔记
        note = Note(
            title=title,
            content=content,
            rating=rating,
            user_id=current_user.id,
            fund_id=fund_id,
            is_public=is_public
        )
        
        db.session.add(note)
        db.session.commit()
        
        flash('笔记创建成功！', 'success')
        return redirect(url_for('web.note_detail', note_id=note.id))
    
    # GET请求
    fund_id = request.args.get('fund_id', type=int)
    preselected_fund = None
    
    if fund_id:
        preselected_fund = Fund.query.get(fund_id)
    
    funds = Fund.query.order_by(Fund.code).all()
    return render_template('create_note.html', funds=funds, preselected_fund=preselected_fund)

@web_bp.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    """编辑笔记页面"""
    note = Note.query.get_or_404(note_id)
    
    # 检查权限
    if note.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        rating = request.form.get('rating', type=int)
        is_public = request.form.get('is_public') == 'on'
        
        if not title or not content:
            flash('请填写所有必填字段', 'danger')
            return render_template('edit_note.html', note=note)
        
        # 更新笔记
        note.title = title
        note.content = content
        note.rating = rating
        note.is_public = is_public
        
        db.session.commit()
        
        flash('笔记更新成功！', 'success')
        return redirect(url_for('web.note_detail', note_id=note.id))
    
    # GET请求
    fund = Fund.query.get(note.fund_id)
    return render_template('edit_note.html', note=note, fund=fund)

@web_bp.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    """删除笔记"""
    note = Note.query.get_or_404(note_id)
    
    # 检查权限
    if note.user_id != current_user.id:
        abort(403)
    
    db.session.delete(note)
    db.session.commit()
    
    flash('笔记已删除', 'success')
    return redirect(url_for('web.my_notes'))

# Purchase records management
@web_bp.route('/purchases')
@login_required
def my_purchases():
    """我的购买记录页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    fund_id = request.args.get('fund_id', type=int)
    
    # 构建查询
    query = Purchase.query.filter_by(user_id=current_user.id)
    
    # 如果指定了基金ID，则过滤
    if fund_id:
        query = query.filter_by(fund_id=fund_id)
        fund = Fund.query.get(fund_id)
    else:
        fund = None
    
    # 按购买日期降序排序
    query = query.order_by(Purchase.purchase_date.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    purchases = pagination.items
    
    return render_template('my_purchases.html', 
                          purchases=purchases, 
                          pagination=pagination, 
                          fund_id=fund_id,
                          fund=fund,
                          get_fund=get_fund)

@web_bp.route('/purchases/create', methods=['GET', 'POST'])
@login_required
def create_purchase():
    """Create a new purchase record."""
    if request.method == 'POST':
        fund_code = request.form.get('fund_code')
        purchase_date = request.form.get('purchase_date')
        amount = request.form.get('amount')
        share = request.form.get('share')
        price = request.form.get('price')
        fee = request.form.get('fee', 0)
        notes = request.form.get('notes', '')
        before_cutoff = request.form.get('before_cutoff') is not None  # This ensures it defaults to True if checked
        
        # Validate required fields
        if not all([fund_code, purchase_date, amount]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('web.create_purchase'))
        
        # 检查基金是否存在
        fund = Fund.query.filter_by(code=fund_code).first()
        if not fund:
            flash('所选基金不存在', 'danger')
            return redirect(url_for('web.create_purchase'))
        
        # 处理日期
        try:
            purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式无效，应为YYYY-MM-DD', 'danger')
            return redirect(url_for('web.create_purchase'))
        
        # Create purchase record
        purchase = Purchase(
            user_id=current_user.id,
            fund_id=fund.id,
            amount=float(amount),
            share=float(share) if share else None,
            price=float(price) if price else None,
            purchase_date=purchase_date_obj,
            fee=float(fee) if fee else 0,
            notes=notes,
            before_cutoff=before_cutoff
        )
        
        db.session.add(purchase)
        db.session.commit()
        
        flash('购买记录创建成功！', 'success')
        return redirect(url_for('web.my_purchases'))
    
    # GET请求
    fund_code = request.args.get('fund_code')
    preselected_fund = None
    
    if fund_code:
        preselected_fund = Fund.query.filter_by(code=fund_code).first()
    
    funds = Fund.query.order_by(Fund.code).all()
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('create_purchase.html', funds=funds, preselected_fund=preselected_fund, today_date=today_date)

@web_bp.route('/purchases/<int:purchase_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_purchase(purchase_id):
    """Edit a purchase record."""
    purchase = Purchase.query.get_or_404(purchase_id)
    
    # Check if the user owns this purchase
    if purchase.user_id != current_user.id:
        flash('您没有权限编辑此记录', 'danger')
        return redirect(url_for('web.my_purchases'))
    
    if request.method == 'POST':
        fund_code = request.form.get('fund_code')
        purchase_date = request.form.get('purchase_date')
        amount = request.form.get('amount')
        share = request.form.get('share')
        price = request.form.get('price')
        fee = request.form.get('fee', 0)
        notes = request.form.get('notes', '')
        before_cutoff = request.form.get('before_cutoff') is not None  # This ensures it defaults to True if checked
        
        # Validate required fields
        if not all([fund_code, purchase_date, amount]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('web.edit_purchase', purchase_id=purchase.id))
        
        # 检查基金是否存在
        fund = Fund.query.filter_by(code=fund_code).first()
        if not fund:
            flash('所选基金不存在', 'danger')
            return redirect(url_for('web.edit_purchase', purchase_id=purchase.id))
        
        # 处理日期
        try:
            purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        except ValueError:
            flash('日期格式无效，应为YYYY-MM-DD', 'danger')
            return redirect(url_for('web.edit_purchase', purchase_id=purchase.id))
        
        # Update purchase record
        purchase.fund_id = fund.id
        purchase.amount = float(amount)
        purchase.share = float(share) if share else None
        purchase.price = float(price) if price else None
        purchase.purchase_date = purchase_date_obj
        purchase.fee = float(fee) if fee else 0
        purchase.notes = notes
        purchase.before_cutoff = before_cutoff
        
        db.session.commit()
        
        flash('购买记录更新成功！', 'success')
        return redirect(url_for('web.my_purchases'))
    
    # GET请求
    fund_code = request.args.get('fund_code')
    preselected_fund = None
    
    if fund_code:
        preselected_fund = Fund.query.filter_by(code=fund_code).first()
    
    funds = Fund.query.order_by(Fund.code).all()
    return render_template('edit_purchase.html', purchase=purchase, funds=funds, preselected_fund=preselected_fund)

@web_bp.route('/purchases/<int:purchase_id>/delete', methods=['POST'])
@login_required
def delete_purchase(purchase_id):
    """删除购买记录"""
    purchase = Purchase.query.get_or_404(purchase_id)
    
    # 检查权限
    if purchase.user_id != current_user.id:
        abort(403)
    
    db.session.delete(purchase)
    db.session.commit()
    
    flash('购买记录已删除', 'success')
    return redirect(url_for('web.my_purchases'))

# Fund value pages
@web_bp.route('/fund/<code>/values')
def fund_values(code):
    """显示基金净值历史"""
    # 获取基金信息
    fund = Fund.query.filter_by(code=code).first_or_404()
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 查询该基金的净值记录
    pagination = FundValue.query.filter_by(fund_id=fund.id)\
        .order_by(FundValue.date.desc())\
        .paginate(page=page, per_page=per_page)
    
    values = pagination.items
    
    # 如果没有净值数据，尝试获取
    if not values and current_user.is_authenticated:
        try:
            fetch_fund_value(fund_code=code)
            # 重新查询
            pagination = FundValue.query.filter_by(fund_id=fund.id)\
                .order_by(FundValue.date.desc())\
                .paginate(page=page, per_page=per_page)
            values = pagination.items
        except Exception as e:
            flash(f'获取基金净值数据失败: {str(e)}', 'danger')
    
    # 获取所有净值数据用于绘制图表
    all_values = FundValue.query.filter_by(fund_id=fund.id)\
        .order_by(FundValue.date.asc())\
        .all()
    
    # 计算各时间段收益率
    performance = calculate_fund_performance(fund.id) if values else {
        'week': None,
        'month': None,
        'three_month': None,
        'six_month': None,
        'year': None,
        'three_year': None,
        'five_year': None,
        'since_inception': None
    }
    
    return render_template('fund_values.html', 
                          fund=fund, 
                          values=values, 
                          pagination=pagination,
                          all_values=all_values,
                          performance=performance)

@web_bp.route('/fund/<code>/refresh-values', methods=['POST'])
@login_required
def refresh_fund_values(code):
    """刷新基金净值数据"""
    # 获取基金信息
    fund = Fund.query.filter_by(code=code).first_or_404()
    
    try:
        count = fetch_fund_value(fund_code=code)
        if count > 0:
            flash(f'成功更新 {count} 条净值数据', 'success')
        else:
            flash('没有新的净值数据可更新', 'info')
    except Exception as e:
        flash(f'更新净值数据失败: {str(e)}', 'danger')
    
    return redirect(url_for('web.fund_values', code=code)) 