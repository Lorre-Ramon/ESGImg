from utils.logger import logger 
import time
import threading
import sys

def pending_animation(message = "Running"):

    animation_chars = "|/-\\"
    i = 0
    while True: 
        sys.stdout.write(f"\r{message} {animation_chars[i % len(animation_chars)]}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1 

# timing decorator
def getRunTime(function_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            
            logger.info(f"运行{function_name}函数")
            
            # start pending_animation daemon thread
            loader_thread = threading.Thread(target=pending_animation, args=(f"运行{function_name}中",))
            loader_thread.daemon = True  # 设置为守护线程
            loader_thread.start()
            
            start = time.time()
            
            try: 
                result = func(*args, **kwargs)
            finally:
                sys.stdout.write("\r" + " " * 40 + "\r")
                sys.stdout.flush()
                
            end = time.time()
            logger.info(f"{function_name}函数耗时: {end - start:.3f}秒")
            print(f"{function_name}函数耗时: {end - start:.3f}秒")
            
            #TODO: 测试平均时长，建立警告机制
            # if ((end - start) > 400) & (function_name == "获取SQL查询结果"): 
            #     logger.warning(f"{function_name}函数耗时过长: {end - start:.3f}秒")
            # if ((end - start) > 200) & (function_name == "添加指标明细"): 
            #     logger.warning(f"{function_name}函数耗时过长: {end - start:.3f}秒")
            return result
        return wrapper
    return decorator 