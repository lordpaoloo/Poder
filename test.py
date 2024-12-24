import http.client

conn = http.client.HTTPSConnection("meta-llama-3-1-405b1.p.rapidapi.com")

payload = "{\"messages\":[{\"role\":\"user\",\"content\":\"Why is the sky blue?\"}]}"

headers = {
    'x-rapidapi-key': "fa2359a385msh865309687fd7284p18e835jsn21e4c7b209b6",
    'x-rapidapi-host': "meta-llama-3-1-405b1.p.rapidapi.com",
    'Content-Type': "application/json"
}

conn.request("POST", "/chat", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))