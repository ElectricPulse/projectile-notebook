import importlib
import traceback
import os

def reload(log_path):
    if os.path.exists(log_path):
        os.remove(log_path)

    os.mkfifo(log_path)
    log = open(log_path, 'w')

    try:
        import main
        importlib.reload(main)
        main.main()
    except Exception as err:
        stack = traceback.format_exc()
        log.write(stack)
    finally:
        log.close()
