from utils.logger import logger 

# timing decorator
def getRunTime(function_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger.info(f"运行{function_name}函数")
            print(f"运行{function_name}函数")
            start = time.time()
            result = func(*args, **kwargs)
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