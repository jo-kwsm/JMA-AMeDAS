import os, shutil
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
save_root_dir = "./data"
dl_dir = os.path.join(os.getcwd(),'dl/')
dl_data_file = os.path.join(dl_dir,"data.csv")
year_init = 2020
year_range = 2
wait_dl = 3
wait_change = 0.5

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
#県のx_pathを辞書で管理
prefectures = {
    '東京都':'//*[@id="pr44"]',
    '沖縄県':'//*[@id="prefectureTable"]/tbody/tr[16]/td',
    '茨城県':'//*[@id="pr40"]',
    '千葉県':'//*[@id="pr45"]',
    '埼玉県':'//*[@id="pr43"]',
    '栃木県':'//*[@id="pr41"]',
    '福島県':'//*[@id="pr36"]',
}
#取得要素のリスト
#テスト時は項目を絞る
#TODO　本番環境は全項目のダウンロード
#TODO　カラム名の指定の仕方
elements = ["気温", "降水量", "日照時間", "風向・風速"]
columns = {
    "気温":["temperature","temperature:quality","temperature:homogeneity"],
    "降水量":["precipitation","precipitation:quality","precipitation:homogeneity"],
    "日照時間":["daylight","daylight:quality","daylight:homogeneity"],
    "風向・風速":["wind_velocity","wind_velocity:quality","wind_direction","wind_direction:quality","wind:homogeneity"],
}
#elements = ["気温", "降水量","降雪の深さ","積雪の深さ","日照時間","風向・風速","全天日射量","現地気圧","海面気圧","相対湿度","蒸気圧","露点温度","天気","雲量","視程"]

#TODO 本番環境はブラウザを開かない
prefs = {
    'download.default_directory' : dl_dir,
    'download.prompt_for_download' : False,
    'download.directory_upgrade' : True,
}

def main():
    #ブラウザ閲覧時のオプションを指定するオブジェクト"options"を作成
    options= Options()
    #必要に応じてオプションを追加
    options.add_experimental_option("prefs",prefs)

    #TODO クラスでドライバーを管理

    #save,dlディレクトリを確認
    if os.path.exists(dl_dir):
        shutil.rmtree(dl_dir)
    os.mkdir(dl_dir)
    if os.path.exists(save_root_dir):
        shutil.rmtree(save_root_dir)
    os.mkdir(save_root_dir)

    for prefecture, prefecture_path in prefectures.items():
        print(prefecture)
        #県名のディレクトリを作成
        save_dir = os.path.join(save_root_dir, prefecture+'/')
        os.mkdir(save_dir)
        #ブラウザのウィンドウを表すオブジェクト"driver"を作成
        driver = webdriver.Chrome(chrome_options=options)
        driver.get(url)
        #立ち上がりを待つ
        time.sleep(wait_change)
        #県の項目に移動
        driver.find_elements_by_xpath(prefecture_path)[0].click()
        time.sleep(wait_change)
        #地区のx_pathを取得
        cities = []
        for to in range(1000):
            path = '//*[@id="stationMap"]/div['+str(to)+']'
            try:
                driver.find_element_by_xpath(path)
            except:
                for id in range(to):
                    cities.append('//*[@id="stationMap"]/div['+str(id)+']/div')
                break
        #エラー項目を辞書で保存
        error_cities = {}

        for city in tqdm(cities):
            #都道府県を選択した場合continue
            city_name = driver.find_element_by_xpath(city).get_attribute("title")
            if city_name[-1] in '都道府県':
                continue
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
                        #column数が合わなければ名前を保存して飛ばす
                        error_cities[city_name]=element
                        error_flag = True
                    data_list.append(tmp_data)
                    #消去
                    os.remove(dl_data_file)
                #各要素を横に結合
                data.append(pd.concat(data_list, axis=1, join='outer'))
            #dataに不備がなければ保存
            if not error_flag:
                #縦に結合
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
        #保存できなかった地域を出力
        for k,v in error_cities.items():
            print(":".join([k,v]))
        #ドライバーを閉じる
        driver.quit()
    
if __name__ == '__main__':
    main()
