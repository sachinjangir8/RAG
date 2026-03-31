import httpx

def test():
    with httpx.Client(timeout=60.0) as client:
        print("Health:", client.get("http://localhost:8000/health").json())
        
        with open("test.txt", "w") as f:
            f.write("The secret passcode is 42. It is required to open the main chamber.")
            
        with open("test.txt", "rb") as f:
            resp = client.post(
                "http://localhost:8000/upload",
                data={"session_id": "test-session"},
                files={"file": f}
            )
            print("Upload:", resp.text)
            
        resp = client.post(
            "http://localhost:8000/chat",
            json={"question": "What is the secret passcode?", "session_id": "test-session"}
        )
        print("Chat:", resp.text)

if __name__ == "__main__":
    test()
