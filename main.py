import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
from cryptography.fernet import Fernet

# TODO economy for 1 route, plan/fact comp
st.set_page_config(layout="wide")

DATAFILE = b'gAAAAABlgvZawmk9a27KdfgJtf9EdsmZWR_YbAmr9J0ac_wK7yq2gZYCi3q08xoX-ePGn8gXaE_CqngjF_FBrZVYvAQI5Oneat-wuXU_6Wdsxh80EvhMN-ExpKRk325OKlnvz_c2OsrKRfZHavPvfFge7VmDVhYwc7Ns-7wBxkKpn6moQYckt74EKocKVisO5Tnb7GPs9RvY9tv4IE0AHCpH9fApWMw44YzfoN-V7KIsPHKC8ZrYnJ092yM3E0l1wmlcn7G9fBWgY7NEQOgtsOl1X98S569dOS3FF2u72Wvn7a9ISbsCGN_05pisWsfhAl3uZ_JrQuNFuVD4HNDiNTR7xNI3nDhGJhWEtsgRPEno72B7d9fhb6UuyVzGVXvVm1bR_nvzSpuP-J9Kqfw0kTI3dvx9pHkriSUw-LPbOXcODEjAJg3x1vh3bR1PcO61ZgfCvHnCEkiTUDtcfixZyzfaUOdVxYc2tJgph1Sac7WsHcNLjkYSdjl3cCL_U0UiezC1lHnNuZk7PS68myCsUvLVvnP_BP3RVWQ-o30JZ-b6Q32i-Ujz1mlLRMIrH4HaM8q7jjIrd-Zx6Lix9A7EjAIT5N6csS6fhPXGQ-FhHVSAyLv8Jcdo2w3r3CJeAsQIRf7H3Xt6uJ5kNIjMOStx8JvwE66s6kvshKuF4_FAAVRPLX6GyeO1Nq53wWwJLxAvV-XLJ2SaP4VfBGjnLcqK7l3Rs8t7Lr4f8RV7IwMy5IR5juzBWDQUKYnEEMH3ii4uOvjyOlICON8fs4vzu-Co6RCLxrqJiqjOVCLoeS-JzU4h7NUPhLUI6Q5tHBaNOH077zVVx_fzXj6E'
@st.cache_data
def load_data(datafile):
    return gpd.read_file(datafile)

def bins(x):
    if x <= 1.5: return "<= 1.5"
    if x <= 2: return "<= 2"
    if x <= 3: return "<= 3"
    if x <= 4: return "<= 4"
    if x <= 5: return "<= 5"
    return "> 5"

if __name__ == "__main__":
    st.title('Дэшборд "Маршруты почты"')
    try: df = load_data(Fernet(st.text_input('Введите пароль:', default='').encode()).decrypt(DATAFILE).decode())
    except ValueError: pass

    if st.checkbox('Показать статистику по РПО и маршрутам'):
        month_no = st.multiselect('Месяц аггрегации данных', df.month_no.unique(), default='2023-10')
        df_stat = df[(df.month_no.isin(month_no)) & (df.region_to != df.region_from)]
        df_stat['Отношение'] = df_stat.len_rel.apply(bins)
        stats = df_stat.groupby('Отношение').agg({'rpo_cnt': 'sum', 'rpo_example': 'count'})
        stats.rpo_cnt = stats.rpo_cnt / df_stat.rpo_cnt.sum() * 100
        stats.rpo_example = stats.rpo_example / df_stat.shape[0] * 100
        st.text('Маршруты с минимум 50 РПО, регион откуда != регион куда')
        st.text('Статистика по отношению длины маршрута к расстоянию по прямой:')
        st.dataframe(stats.rename(columns={'rpo_cnt': 'Доля РПО, %', 'rpo_example': 'Доля маршрутов, %'}))
    col1, col2 = st.columns(2)
    with col1: month_no = st.selectbox('Месяц аггрегации данных', df.month_no.unique())
    with col2: mail_type = st.multiselect('Тип почты', df.mail_type.unique(), default=["Письмо", "Посылка", "EMS РТ", "Отправление EMS", "Посылка онлайн", "ЕКОМ Маркетплейс", "EMS оптимальное", "Мелкий пакет"])
    df = df[(df.mail_type.isin(mail_type)) & (df.month_no == month_no)]
    if st.checkbox('Выбрать начальный и конечный регионы'):
        col1, col2 = st.columns(2)
        with col1: region_from = st.selectbox('Регион откуда', df.region_from.unique())
        with col2: region_to = st.selectbox('Регион куда', df.region_to.unique(), index=15)
        df = df[(df.region_from == region_from) & (df.region_to == region_to)]

    min_rpo = st.slider('Минимум РПО по маршруту', min_value=50, max_value=20000, value=5000, step=50)
    col1, col2 = st.columns(2)
    with col1: min_poly_len = st.slider('Минимальная длина маршрута, КМ', min_value=10, max_value=2000, value=300, step=10)
    with col2: max_poly_len = st.slider('Максимальная длина маршрута, КМ', min_value=min_poly_len, max_value=20000, value=20000, step=100)
    min_len_rel = st.slider('Минимальное отношение длины маршрута к расстоянию между стартом и финишем', min_value=1., max_value=10., value=3., step=0.1)
    select_top = st.slider('Показать топ ... маршрутов по кол-ву РПО', min_value=5, max_value=50, value=20, step=1)

    df = df[(df.rpo_cnt > min_rpo) & (df.len_rel >= min_len_rel) & (df.poly_len >= min_poly_len) & (df.poly_len <= max_poly_len)].sort_values('rpo_cnt', ascending=False).head(select_top)
    df = df.rename(columns={'mail_type': 'тип', 'mail_ctg': 'категория', 'mail_rank': 'разряд', 'rpo_cnt': 'кол-во РПО', 'rpo_example': 'пример РПО', 'route': 'маршрут', 'month_no': 'месяц',
        'obj_sort': 'сортировка на', 'line_len': 'длина напрямик, км', 'poly_len': 'длина маршрута, км', 'len_rel': 'отношение длин', 'region_from': 'регоин откуда', 'region_to': 'регион куда'})
    if st.checkbox('Показать 1 маршрут'):
        route_no = st.slider('Порядковый номер маршрута', min_value=1, max_value=select_top, value=1, step=1)
        try:
            st.text("Пример РПО: " + df.iloc[[route_no-1]]['пример РПО'].iloc[0])
            st_folium(df.iloc[[route_no-1]].explore(column='кол-во РПО', cmap='autumn', legend=True), height=500, use_container_width=True)
        except Exception: st.title('Нет данных, измените фильтры')
    else:
        try: st_folium(df.explore(column='кол-во РПО', cmap='cool', legend=True), height=500, use_container_width=True)
        except Exception: st.title('Нет данных, измените фильтры')
