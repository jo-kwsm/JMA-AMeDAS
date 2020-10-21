import requests
from bs4 import BeautifulSoup
import os, shutil, time, json
from tqdm import tqdm



base_url = "http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no=%s&block_no=&year=&month=&day=&view="
save_dir = "settings/"
prefectures = {}



def get_prefecture(pre_no):
  r = requests.get(base_url%pre_no)
  time.sleep(1)
  soup = BeautifulSoup(r.content, "html.parser")
  pre_name = soup.find('td', class_='nwtop').text.replace("　",'')
  prefectures[pre_name]=pre_no



def main():
  for pre_no in tqdm(range(100)):
    try:
      get_prefecture(pre_no)
    except:
      continue

  json_str = json.dumps(prefectures)
  json_str = json_str.encode("utf-8")
  with open(os.path.join(save_dir,"prefectures.json"), "wb") as f:
    f.write(json_str)
  


if __name__ == "__main__":
  main()
