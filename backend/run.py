import os
import sys

# ========== 修复PyTorch DLL加载问题 - 必须在所有导入之前执行 ==========
venv_base = os.path.dirname(os.path.abspath(__file__))
torch_lib_path = os.path.join(venv_base, '.venv', 'Lib', 'site-packages', 'torch', 'lib')
if os.path.exists(torch_lib_path):
    os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
    if sys.version_info >= (3, 8):
        os.add_dll_directory(torch_lib_path)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'
# ========== PyTorch DLL修复结束 ==========

from app import create_app
from config import Config
import traceback


if __name__ == '__main__':
    print("Starting application...")
    try:
        print("Creating app...")
        app = create_app(Config)
        print("App created successfully")
        
        # 初始化数据库
        print("Initializing database...")
        with app.app_context():
            from models import db
            try:
                db.create_all()
                print("数据库表创建成功")
            except Exception as e:
                print(f"创建数据库表失败：{str(e)}")
                traceback.print_exc()
        
        print("Running app...")
        app.run(debug=False, use_reloader=False)
    except Exception as e:
        print(f"Application error: {str(e)}")
        traceback.print_exc()
