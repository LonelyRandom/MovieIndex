import streamlit as st
from streamlit_gsheets import GSheetsConnection
from login_auth import log_in_auth
from user_1 import complex_home, complex_actress, complex_film

user_1 = st.secrets["indicators"]["USER_1"]

user_3 = st.secrets["indicators"]["USER_3"]


conn = st.connection("gsheets", type=GSheetsConnection)

if 'page' not in st.session_state:
    st.session_state.page = 'login'
    # st.session_state.page = 'home'

if 'usn' not in st.session_state:
    st.session_state.usn = None
    # st.session_state.usn = 'vincent'

if 'check_login' not in st.session_state:
    st.session_state.check_login = False

if st.session_state.page == 'login':
    st.cache_data.clear()
    is_logged_in, usn = log_in_auth(conn)
    st.session_state.check_login = is_logged_in

    if st.session_state.check_login:
        st.session_state.usn = usn
        st.session_state.page = 'home'
        st.rerun()
    else:
        # Tetap di login page, jangan rerun
        st.stop()  

elif st.session_state.page == 'home':
    st.set_page_config(
        layout='wide',
        page_title='Movies Note - Home',
        page_icon='🏠'
    )
    if st.session_state.usn == user_1:
        page = complex_home(conn)
    elif st.session_state.usn == user_3:
        page = complex_home(conn)
    else:
        st.session_state.page = 'login'
        st.session_state.check_login = False
        st.logout()
        st.rerun()
    
    if not page is None:
        st.session_state.page = page
        st.rerun()

elif st.session_state.page == 'film':
    st.set_page_config(
        layout='wide',
        page_title='Movies Note - Film',
        page_icon='🎬'
    )
    if st.session_state.usn == user_1:
        page = complex_film(conn, 'Device 1')
    elif st.session_state.usn == user_3:
        page = complex_film(conn,'Device 2')

    if not page is None:
        st.session_state.page = page
        st.rerun()

elif st.session_state.page == 'actress':
    st.set_page_config(
        layout='wide',
        page_title='Movies Note - Actress',
        page_icon='🌟'
    )
    if st.session_state.usn == user_1:
        page = complex_actress(conn, 'Device 1')
    elif st.session_state.usn == user_3:
        page = complex_actress(conn, 'Device 2')

    if not page is None:
        st.session_state.page = page
        st.rerun()

