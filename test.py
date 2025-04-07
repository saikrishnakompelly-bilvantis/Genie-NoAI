import subprocess
import json

def fetch_csv_with_curl():
   curl_command = [
       "curl",
       "-s",  # silent
       "-H", "Accept: application/vnd.github.v3+json",
       "-H", "Authorization: Bearer <your_token_here>",
       "https://<your-github-enterprise-host>/api/v3/repos/RBS-TOOLING-GIT/Git-hooks-install/contents/installations/installations.csv"
   ]

   result = subprocess.run(curl_command, capture_output=True, text=True)

   if result.returncode == 0:
       try:
           response_json = json.loads(result.stdout)
           content_encoded = response_json.get("content")
           if content_encoded:
               import base64
               csv_content = base64.b64decode(content_encoded).decode('utf-8')
               print("CSV Content:\n", csv_content)
               return csv_content
           else:
               print("No content found in the response.")
       except Exception as e:
           print("Failed to parse JSON or decode content:", e)
   else:
       print("Curl command failed:", result.stderr)

   return None 
