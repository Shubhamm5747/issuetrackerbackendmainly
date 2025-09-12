# from locust import HttpUser, task, between

# class IssueTrackerUser(HttpUser):
#     wait_time = between(1, 3)

#     def on_start(self):
#         # 🔑 Hardcode your JWT access token here
#         self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1NzU5MzY5OCwianRpIjoiOTVkNWM2NzgtYzA5MC00Nzc4LWE2ZWQtMTMzYmYyMzIyNzg3IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NTc1OTM2OTgsImNzcmYiOiJmN2U1Nzg4NC00NzAwLTRkMmEtODIxNS1lY2QwZmI0ODVjNTkiLCJleHAiOjE3NTc1OTcyOTh9.-P5lxgBDCy3_X9B2F7SAtc9oCPaWb9Rm9xQ8MCtoxTE"
#         self.headers = {"Authorization": f"Bearer {self.token}"}

#     @task(2)
#     def list_issues(self):
#         self.client.get("/api/issues", headers=self.headers)

#     @task(1)
#     def create_issue(self):
#         self.client.post("/api/issues/create", headers=self.headers, json={
#             "title": "Locust generated issue",
#             "description": "This issue was created during load testing"
#         })
