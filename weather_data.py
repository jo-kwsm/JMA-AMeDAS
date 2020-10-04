import os, glob, shutil
import pandas as pd
import time
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import chromedriver_binary

#設定
url = "https://www.data.jma.go.jp/gmd/risk/obsdl/index.php"
save_dir = "./data"
dl_dir = os.path.join(os.getcwd(),'dl/')
dl_data_file = os.path.join(dl_dir,"data.csv")
year_init = 2020
year_range = 2
wait_dl = 2

#各ボタンのxpath
area_button = '//*[@id="stationButton"]'
element_button = '//*[@id="elementButton"]'
hour_button = '//*[@id="aggrgPeriod"]/div/div[1]/div[1]/label/input'
period_button = '//*[@id="periodButton"]'
dl_button = '//*[@id="csvdl"]/img'
year_init_button = '//*[@id="chpr1y"]'
year_from_button = '//*[@id="selectPeriod"]/div/div[1]/div[2]/div[2]/select[1]'
year_to_button = '//*[@id="selectPeriod"]/div/div[1]/div[2]/div[3]/select[1]'
city_name_path = '//*[@id="selectedStationList"]/div/div[1]'

#県名のリスト
#TODO　県を指定するx_pathを取得したい
prefectures = ['//*[@id="pr44"]']
#取得要素のリスト
#テスト時は項目を絞る
elements = ["気温", "降水量", "日照時間", "風向・風速"]
columns = {
    "気温":["temperature","temperature:quality","temperature:homogeneity"],
    "降水量":["precipitation","precipitation:quality","precipitation:homogeneity"],
    "日照時間":["daylight","daylight:quality","daylight:homogeneity"],
    "風向・風速":["wind_velocity","wind_velocity:quality","wind_direction","wind_direction:quality","wind:homogeneity"],
}
#TODO　本番環境は全項目のダウンロード
#elements = ["気温", "降水量","降雪の深さ","積雪の深さ","日照時間","風向・風速","全天日射量","現地気圧","海面気圧","相対湿度","蒸気圧","露点温度","天気","雲量","視程"]

#ブラウザ閲覧時のオプションを指定するオブジェクト"options"を作成
options= Options()
#必要に応じてオプションを追加
#TODO 本番環境はブラウザを開かない
prefs = {
    'download.default_directory' : dl_dir,
    'download.prompt_for_download' : False,
    'download.directory_upgrade' : True,
}
options.add_experimental_option("prefs",prefs)

#TODO クラスでドライバーを管理

#save,dlディレクトリを確認
if os.path.exists(dl_dir):
    shutil.rmtree(dl_dir)
os.mkdir(dl_dir)
if os.path.exists(save_dir):
    shutil.rmtree(save_dir)
os.mkdir(save_dir)

for prefecture in prefectures:
    #TODO　県名のディレクトリを作成
    #ブラウザのウィンドウを表すオブジェクト"driver"を作成
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(url)
    #立ち上がりを待つ
    time.sleep(0.5)
    #県の項目に移動
    driver.find_elements_by_xpath(prefecture)[0].click()
    time.sleep(0.5)
    #地区のx_pathを取得
    cities = []
    for to in range(1,1000,2):
        path = '//*[@id="stationMap"]/div['+str(to)+']'
        try:
            driver.find_element_by_xpath(path)
        except:
            for id in range(1,to,2):
                cities.append('//*[@id="stationMap"]/div['+str(id)+']')
            break
    #x_pathから地区名を取得

    for city in tqdm(cities):
        #地区選択
        driver.find_elements_by_xpath(city)[0].click()
        city_name = driver.find_element_by_xpath(city_name_path).text
        error_flag = False
        #要素選択画面に変更
        driver.find_elements_by_xpath(element_button)[0].click()
        #時別に変更
        driver.find_elements_by_xpath(hour_button)[0].click()
        data = []
        
        
        for i in range(year_range):
            if error_flag:
                break
            #期間選択画面に変更
            driver.find_elements_by_xpath(period_button)[0].click()
            if i == 0:
                driver.find_elements_by_xpath(
                    year_init_button)[0].click()
            else:
                #期間を指定
                select_from = Select(driver.find_elements_by_xpath(year_from_button)[0])
                select_to = Select(driver.find_elements_by_xpath(year_to_button)[0])
                select_from.select_by_value(str(year_init-i))
                select_to.select_by_value(str(year_init-i-1))
            data_list = []
            for element in elements:
                if error_flag:
                    break
                #要素選択画面に変更
                driver.find_elements_by_xpath(element_button)[0].click()
                #要素選択
                element_path = '//*[@id="'+element+'"]'
                driver.find_elements_by_xpath(element_path)[0].click()
                #ダウンロード
                driver.find_elements_by_xpath(dl_button)[0].click()
                time.sleep(wait_dl)
                #要素選択解除
                driver.find_elements_by_xpath(element_path)[0].click()
                #読み込み
                tmp_data = pd.read_csv(dl_data_file, encoding="shift-jis", index_col=0, header=None, skiprows=6)
                #columnを変更
                try:
                    tmp_data.columns=columns[element]
                except:
                    print(city_name)
                    error_flag = True
                data_list.append(tmp_data)
                #消去
                os.remove(dl_data_file)
            #各要素を横に結合
            data.append(pd.concat(data_list, axis=1, join='outer'))
        #縦に結合
        if not error_flag:
            data.reverse()
            city_data = pd.concat(data)
            #不要な行を消去
            city_data = city_data.drop_duplicates()
            city_data = city_data.dropna(subset=columns["気温"])
            #地域の名前をつけて保存
            city_data.to_csv(os.path.join(save_dir, city_name+".csv"))
        #地区選択画面に遷移
        driver.find_elements_by_xpath(area_button)[0].click()
        #地区選択解除
        driver.find_elements_by_xpath(city)[0].click()
    #ドライバーを閉じる
    driver.quit()
