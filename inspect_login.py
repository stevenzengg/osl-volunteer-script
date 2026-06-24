import requests
from bs4 import BeautifulSoup

r = requests.get("https://ape.festivol.net/signin.action")
soup = BeautifulSoup(r.text, "html.parser")

print("=== FORMS ===")
for form in soup.find_all("form"):
    print(f"\nForm action: {form.get('action')} | method: {form.get('method')}")
    for inp in form.find_all("input"):
        print(f"  <input name='{inp.get('name')}' type='{inp.get('type')}' value='{inp.get('value', '')}'>")
    for btn in form.find_all("button"):
        print(f"  <button type='{btn.get('type')}' name='{btn.get('name')}'>{btn.text.strip()}</button>")
