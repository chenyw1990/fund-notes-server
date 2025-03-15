from app import create_app, db
from flask.cli import FlaskGroup

app = create_app()
cli = FlaskGroup(app)

@cli.command("init-db")
def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("数据库表已创建！")

if __name__ == '__main__':
    cli() 