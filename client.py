import requests
URL="http://localhost:8000/chat"
def chat_with_agent(user_message):
    payload={"message":user_message}
    try:
        response=requests.post(URL,json=payload)
        if response.status_code==200:
            return response.json()["reply"]
        else:
            return f"后厨出错了，错误代码：{response.status_code}"
    except Exception as e:
        return  f"连接后厨失败，请确认 server.py 还在运行！错误：{e}"
if __name__ == "__main__":
    print("===客户端已启动（输入‘退出’结束）===")
    while True:
        user_input=input("👤 你: ")
        if user_input == "退出":
            break
        reply = chat_with_agent(user_input)
        print(f"🤖 助手: {reply}\n")