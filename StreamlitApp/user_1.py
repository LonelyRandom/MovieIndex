import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import time
import re
from upload_image import upload_to_database, delete_cloudinary_image, rename_cloudinary_image
import pandas as pd
from value_handling import values_handling, initial_load
from dateutil.relativedelta import relativedelta
from streamlit_star_rating import st_star_rating
from st_clickable_images import clickable_images
from streamlit_scroll_to_top import scroll_to_here
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components
import string
from bs4 import BeautifulSoup

# ACTRESS OPTS
REVIEW_OPTS = [
    'Not Watched',
    'Watched'
]

JOB_OPTS = [
    "Actress",
    "Model",
    "Ex-Member",
    "Idol",
    "Singer"
]

COUNTRY_OPTS = [
    "Indonesia",
    "South Korea",
    "Japan",
    "China",
    "Taiwan",
    "Hong Kong"
    "Thailand",
    "Western"
]

# MOVIE OPTS
INFO_OPTS_S = [
    "Want to Watch",
    "On Going",
    "Drop",
    "Complete"
]

INFO_OPTS_M = [
    "Want to Watch",
    "Dissapointing",
    "Drop",
    "Complete"
]

GENRE_OPTS = [
    "Action",
    "Comedy",
    "Drama",
    "Fantasy",
    "Romance",
    "Slice of Life",
    "Thriller",
    "Horror",
    "Live Action",
    "Youth",
    "Mystery",
    "Sci-Fi",
    "Death Game",
    "Documentary",
    "Historical",
    "Political/Law",
    "Sports"
]

TYPE_OPTS = [
    "Movie",
    "Series",
    "TV Show"
]

ROLE_PART_OPTS = [
    'Select Role Part', 
    'Main', 
    'Second', 
    'Support', 
    'Cameo',
    'Guest'
]

TV_PART_OPTS = [
    'Select Role Part',
    'Main Host',
    'Host',
    'Guest',
    'Regular Member'
]

@st.cache_resource
def get_gsheet_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=scope
    )

    return gspread.authorize(creds)


@st.cache_resource()
def film_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["SPREAD_TITLE"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_CODE"]
    )

    return worksheet

@st.cache_resource()
def actress_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["SPREAD_TITLE"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_LIST"]
    )

    return worksheet

@st.cache_resource()
def drama_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["SPREAD_TITLE"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_DRAMA"]
    )

    return worksheet

@st.cache_resource()
def movie_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["SPREAD_TITLE"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_MOVIE"]
    )

    return worksheet

@st.cache_resource()
def tv_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["SPREAD_TITLE"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_TV"]
    )

    return worksheet

@st.cache_resource()
def cast_worksheet():
    client = get_gsheet_client()

    spreadsheet = client.open(
        st.secrets["indicators"]["SPREAD_TITLE"]
    )

    worksheet = spreadsheet.worksheet(
        st.secrets["indicators"]["USER_1_CAST"]
    )

    return worksheet

def parse_jobs_with_group(job_text):
    """
    Return:
    - jobs: list job tanpa [group]
    - groups: dict {job: group_name}
    """
    jobs = []
    groups = {}

    if not job_text or pd.isna(job_text):
        return jobs, groups

    parts = [p.strip() for p in job_text.split(",") if p.strip()]

    for part in parts:
        match = re.match(r"(.*?)\s*\[(.*?)\]", part)
        if match:
            job = match.group(1).strip()
            group = match.group(2).strip()
            jobs.append(job)
            groups[job] = group
        else:
            jobs.append(part)

    return jobs, groups

def format_job_with_groups(jobs, groups):
    result = []

    for job in jobs:
        if job in groups and groups[job]:
            result.append(f"{job} [{groups[job]}]")
        else:
            result.append(job)

    return ", ".join(result)

def init_dataframe_actress():
    """Inisialisasi DataFrame di session state"""
    if "actress_df" not in st.session_state:
        data = actress_worksheet().get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Review', 'Picture', 'Name (Given)', 'Name (Stage)', 'Name (Native)',
                'Birthdate', 'Age', 'Nationality', 'Height (cm)', 'Job',
                'Favourite', 'AsianWiki', 'MDL', 'Gallery'
            ])
        
        st.session_state.actress_df = df
        return df
    else:
        return st.session_state.actress_df

def init_dataframe_film():
    """Inisialisasi DataFrame di session state"""
    if "film_df" not in st.session_state:
        data = film_worksheet().get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Status', 'Info', 'Picture', 'Title', 'Current Episode',
                'Episode', 'Genre', 'Rating', 'Playlist', 'Actress Name', 
                'Note', 'Upload Type', 'Synopsis', 'Roles'
            ])
        
        st.session_state.film_df = df
        return df
    else:
        return st.session_state.film_df    

def init_dataframe_drama():
    """Inisialisasi DataFrame di session state"""
    if "drama_df" not in st.session_state:
        data = drama_worksheet().get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Picture', 'Title', 'Episode', 'Actress', 'Role', 'Year', 'Link',
                'Synopsis', 'Country', 'Aired', 'Cast', 'Cast Name', 'Target Film'
            ])
        
        st.session_state.drama_df = df
        return df
    else:
        return st.session_state.drama_df    

def init_dataframe_movie():
    """Inisialisasi DataFrame di session state"""
    if "movie_df" not in st.session_state:
        data = movie_worksheet().get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Picture', 'Title', 'Actress', 'Role', 'Year', 'Link'
            ])
        
        st.session_state.movie_df = df
        return df
    else:
        return st.session_state.movie_df    

def init_dataframe_tv():
    """Inisialisasi DataFrame di session state"""
    if "tv_df" not in st.session_state:
        data = tv_worksheet().get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Picture', 'Title', 'Episode', 'Actress', 'Role', 'Year', 'Link'
            ])
        
        st.session_state.tv_df = df
        return df
    else:
        return st.session_state.tv_df   

def init_dataframe_cast():
    """Inisialisasi DataFrame di session state"""
    if "cast_df" not in st.session_state:
        data = cast_worksheet().get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Name', 'Picture'
            ])
        
        st.session_state.cast_df = df
        return df
    else:
        return st.session_state.cast_df   
 
def reset_page():
    """Reset halaman ke 1"""
    st.session_state.film_page = 1

def reset_page_actress():
    """Reset halaman ke 1"""
    st.session_state.actress_page = 1

def reset_bank_page():
    """Reset halaman ke 1"""
    st.session_state.bank_page = 1


# --- FUNGSI ALTERNATIF: Grid Layout tanpa Pagination ---
def display_film_grid(df, actress_df, device):
    """
    Menampilkan semua card sekaligus dalam grid
    """

    if 'img_size' not in st.session_state:
        st.session_state.img_size = 'Device 1'

    PLAYLIST_OPTS = ['All'] + sorted(
        df.loc[df['Playlist'] != 'All', 'Playlist']
        .dropna()
        .unique()
        .tolist()
    )

    INFO_OPTS_MIX = ['All'] + sorted(
        df.loc[df['Info'] != 'All', 'Info']
        .dropna()
        .unique()
        .tolist()
    )

    if 'film_page' not in st.session_state:
        st.session_state.film_page = 1

    # Filter data
    filtered_df = df.copy()
    filtered_actress_df = actress_df.copy()
    if st.session_state.get('search_reset', False):
        st.session_state.search_reset = False
        st.session_state.search_bar = ''
        st.session_state.search_text = ''
    if st.session_state.get('set_search', False):
        st.session_state.set_search = False
        st.session_state.search_bar = st.session_state.search_text
        st.session_state.search_text = ''
    with st.container(horizontal=True, vertical_alignment='bottom'):
        search_name = st.text_input("🔍 Search (Title):", placeholder="Enter Movie or Series...", key='search_bar', on_change=reset_page)
        if st.button('Clear', on_click=reset_page):
            st.session_state.search_reset = True
            st.rerun()
    playlist_filter = st.selectbox("Playlist:", options=PLAYLIST_OPTS, on_change=reset_page)
    info_filter = st.selectbox("Info:", options=INFO_OPTS_MIX, on_change=reset_page)

    if device == 'Device 1':
        device_width = 115
        device_height = 163
    else:
        device_width = 106
        device_height = 150


    if search_name:
        mask = (filtered_df['Title'].str.contains(search_name, case=False, na=False) |
                filtered_df['Actress Name'].str.contains(search_name, case=False, na=False))
        filtered_df = filtered_df[mask]

    if playlist_filter != 'All':
        filtered_df = filtered_df[filtered_df['Playlist'] == playlist_filter]  

    if info_filter != 'All':
        filtered_df = filtered_df[filtered_df['Info'] == info_filter]

    total_pages = max(1, (len(filtered_df) + 30 - 1) // 30)  

    def set_page(p):
        st.session_state.film_page = p
    
    if st.session_state.scroll_to_here:
        scroll_to_here(0,key='here')  # Scroll to the top of the page
        st.session_state.scroll_to_here = False
    st.markdown('---')
    if not filtered_df.empty:
        st.markdown(
            f"<div style='text-align:center; font-weight:600;padding-bottom:15px'>Page {st.session_state.film_page}</div>",
            unsafe_allow_html=True
        )

        if total_pages <= 6:
            with st.container(key='page_button', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_top', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_top', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(st.session_state.film_page-1,)):
                    st.session_state.scroll_to_here = True
                
                start_page = max(1, st.session_state.film_page - 1)  
                end_page = min(total_pages, st.session_state.film_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_top', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
            with st.container(horizontal=True):
                if st.button('⏮️ First Page', key='first_top', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(1,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page ⏭️', key='last_top', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(total_pages,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()

                
        
        page = st.session_state.film_page
        
        start_idx = (page - 1) * 30 
        end_idx = min(start_idx + 30, len(filtered_df)) 
        st.markdown("---")
        st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} films")
        rows_to_display = filtered_df.iloc[start_idx:end_idx] 

        st.markdown(
            """
            <style>
            button[data-testid="stBaseButton-tertiary"] p {
                font-size: 13px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        with st.container(horizontal=True, horizontal_alignment='center'):
            for i in range(0, len(rows_to_display)): # len = 8 // i = [0,8]
                if i < len(rows_to_display):
                    film = rows_to_display.iloc[i]
                    real_index = rows_to_display.index[i]

                    if film['Status'] == 'Recommended':
                        title_background_color = 'yellow'
                    else:
                        title_background_color = 'gray'

                    
                    with st.container(width=device_width):
                        # Tambahkan wrapper dengan fixed height
                        st.markdown(f"""
                            <div style="
                                height: {device_height}px;  /* Atur tinggi tetap */
                                width: 100%;
                                overflow: hidden;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                margin-bottom: 10px;
                                border-radius: 5px;
                                border: 1px solid #374151; 
                            ">
                                <img src="{film['Picture']}" 
                                    style="
                                        width: 100%;
                                        height: 100%;
                                        object-fit: cover;
                                        object-position: center;
                                    ">
                            </div>
                        """, unsafe_allow_html=True)

                        title = film['Title']
                        if len(title) > 30:
                            title = title[:30] + "..."
                        if st.button(f':{title_background_color}-background[{title}]', key=f'film_detail_btn_{real_index}', width='stretch', type='tertiary'):
                            st.session_state.viewing_film_index = real_index
                            st.rerun()
                            
        st.markdown('---')
        if total_pages <= 6:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_bottom', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(st.session_state.film_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()

                
                start_page = max(1, st.session_state.film_page - 1)  
                end_page = min(total_pages, st.session_state.film_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_bottom', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,)):
                    st.session_state.scroll_to_here = True   
                    st.rerun()
            with st.container(horizontal=True):
                if st.button('⏮️ First Page', key='first_bottom', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(1,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page ⏭️', key='last_bottom', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(total_pages,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()

    else:
        st.info('No film match the filter')

def display_film_bank(actress_df, drama_df, movie_df, tv_df, device):
    ACTRESS_OPTS = ['No One'] + sorted(
        actress_df.loc[actress_df['Name (Given)'] != 'No One', 'Name (Given)']
        .dropna()
        .unique()
        .tolist()
    )

    if 'bank_page' not in st.session_state:
        st.session_state.bank_page = 1

    filtered_drama_df = drama_df.copy()
    filtered_movie_df = movie_df.copy()
    filtered_tv_df = tv_df.copy()

    selected_actress = st.selectbox('Actress', options=ACTRESS_OPTS, width='stretch', on_change=reset_bank_page, key='bank_actress')

    selected_part = st.radio('Section', options=['Drama', 'Movie', 'TV Show'], horizontal=True, on_change=reset_bank_page, key='bank_section')

    if selected_actress != 'No One':
        filtered_drama_df = filtered_drama_df[filtered_drama_df['Actress'].str.contains(selected_actress, na=False)]
        filtered_movie_df = filtered_movie_df[filtered_movie_df['Actress'].str.contains(selected_actress, na=False)]
        filtered_tv_df = filtered_tv_df[filtered_tv_df['Actress'].str.contains(selected_actress, na=False)]
    

    if 'img_size' not in st.session_state: # useless
        st.session_state.img_size = 'Device 1'
    
    if device == 'Device 1':
        device_width = 115
        device_height = 163
    else:
        device_width = 106
        device_height = 150
    
    if selected_part == 'Drama':
        filtered_df = filtered_drama_df
    elif selected_part == 'Movie':
        filtered_df = filtered_movie_df
    else:
        filtered_df = filtered_tv_df

    total_pages = max(1, (len(filtered_df) + 30 - 1) // 30)

    def set_bank_page(p):
        st.session_state.bank_page = p
    
    if st.session_state.scroll_to_here:
        scroll_to_here(0,key='here')  # Scroll to the top of the page
        st.session_state.scroll_to_here = False
    st.markdown('---')

    if not filtered_df.empty:
        st.markdown(
            f"<div style='text-align:center; font-weight:600;padding-bottom:15px'>Page {st.session_state.film_page}</div>",
            unsafe_allow_html=True
        )

        if total_pages <= 6:
            with st.container(key='page_button', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_bank_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_top', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_top', disabled=(st.session_state.film_page == 1), on_click=set_bank_page, args=(st.session_state.film_page-1,)):
                    st.session_state.scroll_to_here = True
                
                start_page = max(1, st.session_state.bank_page - 1)  
                end_page = min(total_pages, st.session_state.bank_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.bank_page),
                        on_click=set_bank_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_top', disabled=(st.session_state.bank_page == total_pages), on_click=set_bank_page, args=(st.session_state.bank_page+1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
            with st.container(horizontal=True):
                if st.button('⏮️ First Page', key='first_top', disabled=(st.session_state.bank_page == 1), on_click=set_bank_page, args=(1,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page ⏭️', key='last_top', disabled=(st.session_state.bank_page == total_pages), on_click=set_bank_page, args=(total_pages,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()

        page = st.session_state.bank_page
        
        start_idx = (page - 1) * 30 
        end_idx = min(start_idx + 30, len(filtered_df)) 
        st.markdown("---")
        st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} films")
        rows_to_display = filtered_df.iloc[start_idx:end_idx] 

        st.markdown(
            """
            <style>
            button[data-testid="stBaseButton-tertiary"] p {
                font-size: 13px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        with st.container(horizontal=True, horizontal_alignment='center'):
            for i in range(0, len(rows_to_display)): # len = 8 // i = [0,8]
                if i < len(rows_to_display):
                    film = rows_to_display.iloc[i]
                    real_index = rows_to_display.index[i]

                    with st.container(width=device_width):
                        # Tambahkan wrapper dengan fixed height
                        st.markdown(f"""
                            <div style="
                                height: {device_height}px;  /* Atur tinggi tetap */
                                width: 100%;
                                overflow: hidden;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                margin-bottom: 10px;
                                border-radius: 5px;
                                border: 1px solid #374151; 
                            ">
                                <img src="{film['Picture']}" 
                                    style="
                                        width: 100%;
                                        height: 100%;
                                        object-fit: cover;
                                        object-position: center;
                                    ">
                            </div>
                        """, unsafe_allow_html=True)

                        title = film['Title']
                        if len(title) > 30:
                            title = title[:30] + "..."
                        if film['Target Film'] != '--':
                            if st.button(f':green-background[{title}]', key=f'film_detail_btn_{real_index}', width='stretch', type='tertiary'):
                                st.session_state.viewing_bank_index.append([real_index, selected_part])
                                st.rerun()
                        else:
                            if st.button(f':gray-background[{title}]', key=f'film_detail_btn_{real_index}', width='stretch', type='tertiary'):
                                st.session_state.viewing_bank_index.append([real_index, selected_part])
                                st.rerun()
                            
        st.markdown('---')
        if total_pages <= 6:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.bank_page),
                        on_click=set_bank_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_bottom', disabled=(st.session_state.bank_page == 1), on_click=set_bank_page, args=(st.session_state.bank_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()

                
                start_page = max(1, st.session_state.bank_page - 1)  
                end_page = min(total_pages, st.session_state.bank_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_pages - 3), total_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.bank_page),
                        on_click=set_bank_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_bottom', disabled=(st.session_state.bank_page == total_pages), on_click=set_bank_page, args=(st.session_state.bank_page+1,)):
                    st.session_state.scroll_to_here = True   
                    st.rerun()
            with st.container(horizontal=True):
                if st.button('⏮️ First Page', key='first_bottom', disabled=(st.session_state.bank_page == 1), on_click=set_bank_page, args=(1,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page ⏭️', key='last_bottom', disabled=(st.session_state.bank_page == total_pages), on_click=set_bank_page, args=(total_pages,), width='stretch'):
                    st.session_state.scroll_to_here = True
                    st.rerun()

    else:
        st.info('No film match the filter')



def complex_home(conn):
    if 'log_out_btn' not in st.session_state:
        st.session_state.log_out_btn = False

    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Home Page</h1>", unsafe_allow_html=True)
    df_actress = init_dataframe_actress()
    df_film = init_dataframe_film()

    left, right = st.columns(2)
    with left:
        with st.container(key='ActressList'):
            st.header('🌟 Actress List')
            with st.container(horizontal=True):
                with st.container(key='Actress Info 1', horizontal=False):
                    st.metric('Actress Count' , len(df_actress))
                    st.metric('Watched',len(df_actress[df_actress['Review'] == 'Watched']))
                with st.container(key='Actress Info 2', horizontal=False):
                    st.metric('Not Watched', len(df_actress[df_actress['Review'] == 'Not Watched']))
                    st.metric('Favourite', len(df_actress[df_actress['Favourite'] == 1]))
            if st.button('Go To Actress →'):
                return 'actress'
    with right:
        with st.container(key='FilmList'):
            st.header('🎬 Film List')
            with st.container(horizontal=True):
                with st.container(key='Film Info 1', horizontal=False):
                    st.metric('Film Count', len(df_film))
                    st.metric('Watched', len(df_film[df_film['Status'] == 'Watched']))
                with st.container(key='Film Info 2', horizontal=False):
                    st.metric('Not Watched', len(df_film[df_film['Status'] == 'Not Watched']))
                    st.metric('Recommended', len(df_film[df_film['Status'] == 'Recommended']))
            if st.button('Go To Film →'):
                return 'film'
    
    if st.session_state.log_out_btn == False:
        if st.button('🔐 Logout', width='stretch', type='primary'):
            st.session_state.log_out_btn = True
            st.rerun()
    else:
        st.warning('Are you sure want to logout?')
        with st.container(horizontal=True):
            if st.button('Yes', width='stretch'):
                st.session_state.log_out_btn = False
                st.logout()
                return 'login'
            if st.button('No', width='stretch'):
                st.session_state.log_out_btn = False
                st.rerun()
    
    # CSS custom untuk container tertentu
    st.markdown("""
    <style>
    /* Container dengan key ActressList */
    .st-key-ActressList {
        background-color: #EC4899;
        padding: 30px 20px 50px 20px;
        border-radius: 10px;
    }

    .st-key-MainContainer {
        background-color: #e6e7f2; /* Pink soft */
        padding: 30px 20px 50px 20px;
        border-radius: 10px;
    }
                
    /* Container dengan key FilmList */
    .st-key-FilmList {
        background-color: #22D3EE; /* Pink soft */
        padding: 30px 20px 50px 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def set_eps(p, max_p):
    if p>0 and p<=max_p:
        st.session_state.eps = p
    
    if st.session_state.eps == max_p:
        st.session_state.info = 'complete'
    else:
        st.session_state.info = 'on going'

def set_rec():
    st.session_state.rec = st.session_state.rec_eps

def complex_film(conn, device):
    # Inisialisasi variabel kontrol
    if "editing_film_index" not in st.session_state:
        st.session_state.editing_film_index = None
    if "viewing_film_index" not in st.session_state:
        st.session_state.viewing_film_index = None
    if "viewing_bank_index" not in st.session_state:
        st.session_state.viewing_bank_index = []
    if 'scroll_to_top' not in st.session_state:
        st.session_state.scroll_to_top = False
    if 'scroll_to_here' not in st.session_state:
        st.session_state.scroll_to_here = False
    if 'delete_film' not in st.session_state:
        st.session_state.delete_film = False
    if 'edit_eps' not in st.session_state:
        st.session_state.edit_eps = False
    if 'eps' not in st.session_state:
        st.session_state.eps = 0
    if 'info' not in st.session_state:
        st.session_state.info = None
    if 'rec' not in st.session_state:
        st.session_state.rec = False

    if 'show_more_main' not in st.session_state:
        st.session_state.show_more_main = False
    if 'show_more_support' not in st.session_state:
        st.session_state.show_more_support = False
    if 'show_more_guest' not in st.session_state:
        st.session_state.show_more_guest = False
    if 'show_more_cameo' not in st.session_state:
        st.session_state.show_more_cameo = False
    

    if st.session_state.scroll_to_top:
        scroll_to_here(0,key='top')  # Scroll to the top of the page
        st.session_state.scroll_to_top = False
    if 'film_df' not in st.session_state:
        st.session_state.film_df = init_dataframe_film()
    
    df = st.session_state.film_df


    if 'actress_df' not in st.session_state:
        st.session_state.actress_df = init_dataframe_actress()

    actress_df = st.session_state.actress_df

    if 'drama_df' not in st.session_state:
        st.session_state.drama_df = init_dataframe_drama()

    drama_df = st.session_state.drama_df

    if 'movie_df' not in st.session_state:
        st.session_state.movie_df = init_dataframe_movie()

    movie_df = st.session_state.movie_df

    if 'tv_df' not in st.session_state:
        st.session_state.tv_df = init_dataframe_tv()

    tv_df = st.session_state.tv_df

    if 'cast_df' not in st.session_state:
        st.session_state.cast_df = init_dataframe_cast()

    cast_df = st.session_state.cast_df



    PLAYLIST_OPTS = ['All'] + sorted(
        df.loc[df['Playlist'] != 'All', 'Playlist']
        .dropna()
        .unique()
        .tolist()
    )
    
    TITLE_OPTS = ['New'] + sorted(
        df.loc[df['Title'] != 'All', 'Title']
        .dropna()
        .unique()
        .tolist()
    )

    ACTRESS_OPTS = ['No One'] + sorted(
        actress_df.loc[actress_df['Name (Stage)'] != 'No One', 'Name (Stage)']
        .dropna()
        .unique()
        .tolist()
    )

    @st.dialog("🎬 Film Details", width='small')
    def show_film_details():
        if st.session_state.viewing_bank_index != []:
            show_bank_film(st.session_state.viewing_bank_index)
        else:
            index = st.session_state.viewing_film_index

            if index is None or index >= len(df):
                st.warning("No film selected")
                st.stop()
            if st.session_state.editing_film_index == index:
                show_edit_film(index)
            else:
                show_view_film(index)

    def show_bank_film(view_bank):
        index = view_bank[0][0]
        type = view_bank[0][1]
        if type == 'Drama':
            film = st.session_state.drama_df.loc[index]
        elif type == 'Movie':
            film = st.session_state.movie_df.loc[index]
        else:
            film = st.session_state.tv_df.loc[index]

        with st.container(key='poster_code', horizontal_alignment='center'):
            st.markdown(f"<h2 style='text-align: center;'>{film['Title']}</h2>", unsafe_allow_html=True)
            st.image(film['Picture'], width=200)
        
            st.link_button('Film Detail', film['Link'], type='primary', width=200)
        filtered_actress_df = actress_df.copy()

        actress_list = film['Actress'].split('_ ')
        matching_actresses = filtered_actress_df[filtered_actress_df['Name (Stage)'].isin(actress_list)]
        if len(matching_actresses)>2:
            is_center = 'center'
        else:
            is_center = 'left'
        st.markdown('---')
        roles_is_empty = pd.isna(film['Role']) or film['Role'] == '--'
        if not roles_is_empty:
            actress_role_data = []
            roles_data = film['Role']
            roles_list = roles_data.split(' ## ')
            for actress_data in roles_list:
                actress_role = actress_data.split('_ ')
                new_row = [
                    actress_role[0],
                    actress_role[1],
                    actress_role[2]
                ]
                actress_role_data.append(new_row)
            actress_role_df = pd.DataFrame(actress_role_data, columns=['Name', 'Role Name', 'Role Part'])
        st.markdown("<h3 style='text-align: center; font-size:20px; padding-bottom:10px; margin-bottom:0px;'>Actress</h3>", unsafe_allow_html=True)
        for idx in matching_actresses.index:
            if type == 'Drama' or type == 'Movie':
                actress_name = matching_actresses['Name (Stage)'][idx]
                container_key = f"{actress_name}_{index+1}_photo"
                if st.button(f':orange-background[**{actress_name}**]', width='content', type='tertiary', key=f"{actress_name}_{idx}", on_click=reset_page):
                    st.session_state.viewing_film_index = None
                    st.session_state.editing_film_index = None
                    st.session_state.search_text = actress_name
                    st.session_state.set_search = True
                    st.session_state.scroll_to_top = True
                    st.rerun()
                with st.container(horizontal=True, horizontal_alignment=is_center):
                    with st.container(width=80, key=container_key):
                        # Display image as circle using HTML
                        st.markdown(f"""
                            <div style="
                                width: 70px;
                                height: 70px;
                                border-radius: 50%;
                                overflow: hidden;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                margin: 0 auto 8px auto;
                                background: white;
                                border: 1px solid #374151;
                            ">
                                <img src="{matching_actresses['Picture'][idx]}" 
                                    style="
                                        width: 100%;
                                        height: 100%;
                                        object-fit: cover;
                                    ">
                            </div>
                        """, unsafe_allow_html=True)
                        
                    
                    with st.container():
                        if not roles_is_empty:
                            roles = actress_role_df[actress_role_df['Name'] == actress_name].iloc[0]
                            if roles['Role Name'] != '--':
                                st.write(f'**Role Name :** :gray-background[{roles["Role Name"]}]')
                            else:
                                st.write('**Role Name :** :yellow[(No Info)]')
                            
                            if roles['Role Part'] != '--':
                                st.write(f'**Role Part :** :gray-background[{roles["Role Part"]}]')
                            else:
                                st.write('**Role Part :** :yellow[(No Info)]')
                        else:
                            st.write('**Role Name :** :yellow[(No Info)]')
                            st.write('**Role Part :** :yellow[(No Info)]')
            else:
                with st.container(horizontal=True, horizontal_alignment=is_center):
                    for idx in matching_actresses.index:
                        actress_name = matching_actresses['Name (Given)'][idx]
                        container_key = f"container_{actress_name}_{index}"
                        with st.container(width=80, key=container_key):
                            # Display image as circle using HTML
                            st.markdown(f"""
                                <div style="
                                    width: 70px;
                                    height: 70px;
                                    border-radius: 50%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    margin: 0 auto 8px auto;
                                    background: white;
                                    border: 1px solid #374151;
                                ">
                                    <img src="{matching_actresses['Picture'][idx]}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                        ">
                                </div>
                            """, unsafe_allow_html=True)
                            # Button
                            if st.button(actress_name, width='stretch', type='tertiary', key=f"{actress_name}_{idx}", on_click=reset_page):
                                st.session_state.viewing_film_index = None
                                st.session_state.editing_film_index = None
                                st.session_state.search_text = actress_name
                                st.session_state.set_search = True
                                st.session_state.scroll_to_top = True
                                st.rerun()

                        
        if 'No One' in actress_list:
            with st.container(width=80):
                st.markdown(f"""
                    <div style="
                        width: 70px;
                        height: 70px;
                        border-radius: 50%;
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0 auto 8px auto;
                        background: white;
                        border: 1px solid #374151;
                    ">
                        <img src="{st.secrets.indicators.PLACEHOLDER_IMG}" 
                            style="
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                            ">
                    </div>
                """, unsafe_allow_html=True)
                
                # Button
                if st.button('No One', width='stretch', type='tertiary', 
                            key=f"no_one", on_click=reset_page):
                    st.session_state.viewing_film_index = None
                    st.session_state.editing_film_index = None
                    st.session_state.search_text = 'No One'
                    st.session_state.set_search = True
                    st.session_state.scroll_to_top = True
                    st.rerun()

        with st.expander('Other Cast', width='stretch'):
            cast_role_data = []
            main_role = []
            support_role = []
            guest_role = []
            cameo_role = []
            cast_list = film['Cast Name'].split(' ## ')
            actress_list = film['Actress'].split('_ ')
            for cast_data in cast_list:
                cast_role = cast_data.split('_ ')
                if cast_role[0] not in actress_list:
                    if cast_role[2] == 'Main Role':
                        main_role.append([
                            cast_role[0],
                            cast_role[1],
                            cast_role[2]
                        ])
                    elif cast_role[2] == 'Support Role':
                        support_role.append([
                            cast_role[0],
                            cast_role[1],
                            cast_role[2]
                        ])
                    elif cast_role[2] == 'Guest Role':
                        guest_role.append([
                            cast_role[0],
                            cast_role[1],
                            cast_role[2]
                        ])
                    elif cast_role[2] == 'Cameo':
                        cameo_role.append([
                            cast_role[0],
                            cast_role[1],
                            cast_role[2]
                        ])
            
            st.write('**Main Role**')
            if main_role:
                for main in main_role:
                    with st.container(horizontal=True, horizontal_alignment='left'):
                        st.write(f'- **:gray-background[{main[0]}]** : :yellow-background[{main[1]}] :orange-background[({main[2]})]')
            else:
                st.write('--')
                

            st.write('**Support Role**')
            if support_role:
                for support in support_role:
                    st.write(f'- **:gray-background[{support[0]}]** : :yellow-background[{support[1]}] :orange-background[({support[2]})]')
            else:
                st.write('--')
            
            st.write('**Guest Role**')
            if guest_role:
                for guest in guest_role:
                    st.write(f'- **:gray-background[{guest[0]}]** : :yellow-background[{guest[1]}] :orange-background[({guest[2]})]')
            else:
                st.write('--')
                    
            st.write('**Cameo**')
            if cameo_role:
                for cameo in cameo_role:
                    st.write(f'- **:gray-background[{cameo[0]}]** : :yellow-background[{cameo[1]}] :orange-background[({cameo[2]})]')
            else:
                st.write('--')

        st.markdown('---')
        st.markdown("<h3 style='text-align: center; font-size:18px; padding-bottom:10px; margin-bottom:0px;'>Synopsis</h3>", unsafe_allow_html=True)
        st.text(film['Synopsis'],text_alignment='justify')

        st.markdown('---')
        with st.container(horizontal=True, horizontal_alignment='center'):
            if type != 'Movie':
                eps = film['Episode']
            else:
                eps = 'Movie'
            st.markdown(
                f"""
                <div style="
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 10px;
                    padding: 12px;
                    text-align: center;
                ">
                    <div style="font-size: 14px; color: gray;">
                        Year
                    </div>
                    <div style="font-size: 28px; font-weight: bold;">
                        {film['Year']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(
                f"""
                <div style="
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 10px;
                    padding: 12px;
                    text-align: center;
                ">
                    <div style="font-size: 14px; color: gray;">
                        Episode
                    </div>
                    <div style="font-size: 28px; font-weight: bold;">
                        {eps}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown(
            f"""
            <div style="
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 10px;
                padding: 12px;
                text-align: center;
            ">
                <div style="font-size: 14px; color: gray;">
                    Country
                </div>
                <div style="font-size: 28px; font-weight: bold;">
                    {film['Country']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div style="
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 10px;
                padding: 12px;
                text-align: center;
            ">
                <div style="font-size: 14px; color: gray;">
                    Aired On
                </div>
                <div style="font-size: 28px; font-weight: bold;">
                    {film['Aired']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        title_index = TITLE_OPTS.index(film['Target Film']) if film['Target Film'] in TITLE_OPTS else 0

        target = st.selectbox('Film Target', options=TITLE_OPTS, width='stretch', index=title_index)    
        st.markdown('---')
        if st.button('➕ Add Film', width='stretch'):
            if target != 'New':
                target_data = df[df['Title'] == target].iloc[0]
                target_index = df[df['Title'] == target].index[0]
                if target_data['Type'] == 'Series' or target_data['Type'] == 'TV Show':
                    film_curr_eps = target_data['Current Episode']
                    film_eps = target_data['Episode']
                else:
                    film_curr_eps = '?'
                    film_eps = '?'
                
                row = target_index+2
                new_row = [
                    target_data['Status'],
                    target_data['Info'],
                    target_data['Picture'],
                    target_data['Title'],
                    target_data['Type'],
                    film_curr_eps,
                    film_eps,
                    target_data['Genre'],
                    target_data['Rating'],
                    target_data['Playlist'],
                    target_data['Actress Name'],
                    target_data['Note'],
                    target_data['Upload Type'],
                    film['Synopsis'],
                    target_data['Roles'],
                    film['Year'],
                    film['Aired'],
                    film['Cast'],
                    film['Cast Name'],
                    film['Link']
                ]

                if film_worksheet().update(f'A{row}:T{row}', [new_row]):
                    st.session_state.film_df.loc[target_index] = new_row
                    row = index + 2
                    if type == 'Drama':
                        drama_worksheet().update(f'M{row}', target)
                        st.session_state.drama_df.at[index, 'Target Film'] = target
                    elif type == 'Movie':
                        movie_worksheet().update(f'M{row}', target)
                        st.session_state.movie_df.at[index, 'Target Film'] = target
                    elif type == 'TV Show':
                        tv_worksheet().update(f'M{row}', target)
                        st.session_state.tv_df.at[index, 'Target Film'] = target
            else:
                if type == 'Drama':
                    episode = str(film['Episode'])
                    playlist = film['Country'] + ' Series'
                elif type == 'Movie':
                    episode = '?'
                    playlist = film['Country'] + ' Movies'
                else:
                    episode = str(film['Episode'])
                    playlist = 'Variety Show'

                new_row = [
                    "Not Watched",
                    "Want to watch",
                    "https://res.cloudinary.com/devooeuej/image/upload/v1765969908/placeholder_poster.jpg",
                    film['Title'],
                    type,
                    "?",
                    episode,
                    "--",
                    "?",
                    playlist,
                    film['Actress'],
                    '--',
                    'Local',
                    film['Synopsis'],
                    film['Role'],
                    str(film['Year']),
                    film['Aired'],
                    film['Cast'],
                    film['Cast Name'],
                    film['Link']
                ]

                if film_worksheet().append_row(new_row):
                    st.session_state.film_df.loc[target_index] = new_row
                    row = index + 2
                    if type == 'Drama':
                        drama_worksheet().update(f'M{row}', film['Title'])
                        st.session_state.drama_df.at[index, 'Target Film'] = film['Title']
                    elif type == 'Movie':
                        movie_worksheet().update(f'L{row}', film['Title'])
                        st.session_state.movie_df.at[index, 'Target Film'] = film['Title']
                    elif type == 'TV Show':
                        tv_worksheet().update(f'M{row}', film['Title'])
                        st.session_state.tv_df.at[index, 'Target Film'] = film['Title']
            st.toast('✅ Successfully added data to film!')
            time.sleep(.5)  
            st.session_state.viewing_bank_index = []
            st.rerun()

        if st.button('Close', width='stretch', type='primary'):
            st.session_state.viewing_bank_index = []
            st.rerun()

    def show_view_film(index):
        film = df.iloc[index]
        filtered_actress_df = actress_df.copy()

        actress_list = film['Actress Name'].split('_ ')
        matching_actresses = filtered_actress_df[filtered_actress_df['Name (Stage)'].isin(actress_list)]
        tab_film_data, tab_other_cast, tab_cast_setting = st.tabs(['Film Info', 'Other Cast', 'Cast Setting'])
        if film['Roles'] != 'Unqualified':
            for act in actress_list:
                st.markdown(f"""
                <style>
                div[data-testid="stVerticalBlock"]:has(p:contains("{act}")) button p {{
                    font-size: 15px !important;
                    padding-top: 20px !important;
                }}
                </style>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                """
                <style>
                button[data-testid="stBaseButton-tertiary"] p {
                    font-size: 14px !important;
                    color: #d6cfc7 !important;
                }
                """,
                unsafe_allow_html=True
            )
        with tab_film_data:
            with st.container(key='poster_code', horizontal_alignment='center'):
                st.markdown(f"<h2 style='text-align: center;'>{film['Title']}</h2>", unsafe_allow_html=True)
                st.image(film['Picture'], width=200)
            
                film_trailer = 'https://www.youtube.com/results?search_query=' + '+'.join(film['Title'].lower().split(' ')) + '+trailer'
                st.link_button('Trailer', film_trailer, type='primary', width=200)
            with st.expander('Synopsis'):
                if pd.notna(film['Synopsis']):
                    text_synopsis = film['Synopsis']
                else:
                    text_synopsis = '⚠️ Synopsis not found!'
                st.write(text_synopsis)
            if len(matching_actresses)>2:
                is_center = 'center'
            else:
                is_center = 'left'
            st.markdown('---')

            if film['Roles'] != 'Unqualified':
                st.markdown("<h3 style='text-align: center; font-size:20px; padding-bottom:0px; margin-bottom:0px;'>Actress</h3>", unsafe_allow_html=True)
                roles_is_empty = pd.isna(film['Roles']) or film['Roles'] == '--'
                if not roles_is_empty:
                    actress_role_data = []
                    cast_role_data = []
                    roles_data = film['Roles']
                    roles_list = roles_data.split(' ## ')
                    for actress_data in roles_list:
                        actress_role = actress_data.split('_ ')
                        new_row = [
                            actress_role[0],
                            actress_role[1],
                            actress_role[2]
                        ]
                        actress_role_data.append(new_row)
                    actress_role_df = pd.DataFrame(actress_role_data, columns=['Name', 'Role Name', 'Role Part'])
                    if film['Cast Name'] != '--':
                        cast_data = film['Cast Name']
                        cast_list = cast_data.split(' ## ')
                        st.write(cast_list)
                        for actress_data in cast_list:
                            actress_role = actress_data.split('_ ')
                            actress_name = cast_df.loc[cast_df['Link'] == actress_role[0], 'Target Name']
                            if actress_name.iloc[0] == '--':
                                actress_name = cast_df.loc[cast_df['Link'] == actress_role[0], 'Name'].iloc[0]

                            new_row = [
                                actress_name,
                                actress_role[1],
                                actress_role[2]
                            ]
                            cast_role_data.append(new_row)
                        cast_role_df = pd.DataFrame(cast_role_data, columns=['Name', 'Role Name', 'Role Part'])
                for idx in matching_actresses.index:
                    actress_name = matching_actresses['Name (Stage)'][idx]
                    container_key = f"{actress_name}_{index}"
                    if matching_actresses["Name (Given)"][idx] == actress_name:
                        button_label = actress_name
                    else:
                        button_label = actress_name + " / " + matching_actresses["Name (Given)"][idx]

                    

                    with st.container(horizontal=True):
                        if st.button(f':orange-background[**{button_label}**]', width='content', type='tertiary', key=f"{actress_name}_{idx}", on_click=reset_page):
                            st.session_state.viewing_film_index = None
                            st.session_state.editing_film_index = None
                            st.session_state.search_text = actress_name
                            st.session_state.set_search = True
                            st.session_state.scroll_to_top = True
                            st.rerun()
                        if film['Cast Name'] != '--':
                            if actress_name in cast_role_df['Name'].values and '--' in actress_role_df.loc[actress_role_df['Name'] == actress_name, 'Role Part'].values and '--' in actress_role_df.loc[actress_role_df['Name'] == actress_name, 'Role Name'].values:
                                if st.button('✅', type='tertiary', key=f'exist_role_{idx}'):
                                    match_cast = cast_role_df[cast_role_df['Name'] == actress_name]
                                    match_act = actress_role_df[actress_role_df['Name'] == actress_name].index[0]
                                    final_actress_df = actress_role_df.copy()
                                    final_actress_df.loc[match_act] = match_cast.values
                                    updated_cast = []
                                    for i in range(len(final_actress_df)):
                                        data = final_actress_df.iloc[i]
                                        updated_cast.append(f"{data['Name']}_ {data['Role Name']}_ {data['Role Part']}")
                                    updated_cast = ' ## '.join(updated_cast)
                                    if film_worksheet().update(f'O{index+2}', updated_cast):
                                        df.at[index, 'Roles'] = updated_cast
                                        st.session_state.film_df = df
                                        st.rerun()
                                        
                    with st.container(horizontal=True, horizontal_alignment=is_center):
                        with st.container(width=80, key=container_key):
                            # Display image as circle using HTML
                            st.markdown(f"""
                                <div style="
                                    width: 70px;
                                    height: 70px;
                                    border-radius: 50%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    margin: 0 auto 8px auto;
                                    background: white;
                                    border: 1px solid #374151;
                                ">
                                    <img src="{matching_actresses['Picture'][idx]}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                        ">
                                </div>
                            """, unsafe_allow_html=True)
                            
                        
                        with st.container():
                            if not roles_is_empty:
                                roles = actress_role_df[actress_role_df['Name'] == actress_name].iloc[0]
                                if roles['Role Name'] != '--':
                                    st.write(f'**Role Name :** :gray-background[{roles["Role Name"]}]')
                                else:
                                    st.write('**Role Name :** :yellow[(No Info)]')
                                
                                if roles['Role Part'] != '--':
                                    st.write(f'**Role Part :** :gray-background[{roles["Role Part"]}]')
                                else:
                                    st.write('**Role Part :** :yellow[(No Info)]')
                            else:
                                st.write('**Role Name :** :yellow[(No Info)]')
                                st.write('**Role Part :** :yellow[(No Info)]')

            else:
                st.markdown("<h3 style='text-align: center; font-size:20px; padding-bottom:0px; margin-bottom:10px;'>Actress</h3>", unsafe_allow_html=True)
                with st.container(horizontal=True, horizontal_alignment=is_center):
                    for idx in matching_actresses.index:
                        actress_name = matching_actresses['Name (Stage)'][idx]
                        if actress_name == matching_actresses['Name (Given)'][idx]:
                            button_label = actress_name
                        else:
                            button_label = actress_name + ' / ' + matching_actresses['Name (Given)'][idx]

                        container_key = f"{actress_name}_{index}"
                        with st.container(width=80, key=container_key):
                            # Display image as circle using HTML
                            st.markdown(f"""
                                <div style="
                                    width: 70px;
                                    height: 70px;
                                    border-radius: 50%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    margin: 0 auto 8px auto;
                                    background: white;
                                    border: 1px solid #374151;
                                ">
                                    <img src="{matching_actresses['Picture'][idx]}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                        ">
                                </div>
                            """, unsafe_allow_html=True)
                            # Button
                            if st.button(button_label, width='stretch', type='tertiary', key=f"{actress_name}_{idx}", on_click=reset_page):
                                st.session_state.viewing_film_index = None
                                st.session_state.editing_film_index = None
                                st.session_state.search_text = actress_name
                                st.session_state.set_search = True
                                st.session_state.scroll_to_top = True
                                st.rerun()
                            
            if 'No One' in actress_list:
                with st.container(width=80):
                    st.markdown(f"""
                        <div style="
                            width: 70px;
                            height: 70px;
                            border-radius: 50%;
                            overflow: hidden;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            margin: 0 auto 8px auto;
                            background: white;
                            border: 1px solid #374151;
                        ">
                            <img src="{st.secrets.indicators.PLACEHOLDER_IMG}" 
                                style="
                                    width: 100%;
                                    height: 100%;
                                    object-fit: cover;
                                ">
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Button
                    if st.button('No One', width='stretch', type='tertiary', 
                                key=f"no_one", on_click=reset_page):
                        st.session_state.viewing_film_index = None
                        st.session_state.editing_film_index = None
                        st.session_state.search_text = 'No One'
                        st.session_state.set_search = True
                        st.session_state.scroll_to_top = True
                        st.rerun()

            st.markdown('---')
            info_text = film['Info']
            status_text = film['Status']
            type_text = film['Type']

            if info_text == 'Complete':
                info_icon = '🔵'
                info_color = 'blue'
            elif info_text == 'Want to Watch':
                info_icon = '🟢'
                info_color = 'green'
            elif info_text == 'On Going':
                info_icon = '🟡'
                info_color = 'yellow'
            elif info_text == 'Drop':
                info_icon = '🔴'
                info_color = 'red'
            elif info_text == 'Dissapointing':
                info_icon = '🟣'
                info_color = 'violet'
            else:
                info_icon = '⚪'
                info_color = 'grey'

            if status_text == 'Not Watched':
                status_icon = '🔴'
                status_color = 'red'
            elif status_text == 'Watched':
                status_icon = '🟢'
                status_color = 'green'
            elif status_text == 'Recommended':
                status_icon = '🟣'
                status_color = 'violet'
            else:
                status_icon = '⚪'
                status_color = 'grey'

            if type_text == 'Movie':
                type_icon = '🎬'
            else:
                type_icon = '🎞️'

            with st.container(horizontal=True):
                with st.container():
                    st.markdown('### Status')
                    if st.session_state.info is None:
                        st.badge(film['Status'], icon=status_icon, color=status_color)
                    else:
                        if st.session_state.rec:
                            st.badge('Recommended', icon='🟣', color='violet')
                        else:
                            st.badge('Watched', icon='🟢', color='green')

                    st.markdown('### Type')
                    st.badge(film['Type'], icon=type_icon, color='orange')

                    st.markdown('### Genre')
                    st.write(film['Genre'])
            
                with st.container():
                    st.markdown('### Info')
                    if st.session_state.info is None:
                        st.badge(film['Info'], icon=info_icon, color=info_color)
                    else:
                        if st.session_state.eps == int(film['Episode']):
                            st.badge('Complete', icon='🔵', color='blue')
                        else:
                            st.badge('On Going', icon='🟡', color='yellow')


                    st.markdown('### Episode')
                    if type_text == 'Movie':
                        st.write('--')
                    else:
                        with st.container(horizontal=True, horizontal_alignment='left'):
                            if not st.session_state.edit_eps:
                                with st.container(width=30):
                                    st.markdown(
                                        f"""
                                        <div style="
                                            display: flex;
                                            align-items: center;
                                            height: 40px;
                                            font-size: 16px;
                                        ">
                                            {film['Current Episode']}/{film['Episode']}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                if film['Info'] != 'Complete':
                                    if st.button('✏️', key='edit-eps', type='tertiary'):
                                        if film['Current Episode'] == '?':
                                            eps = 1
                                            st.session_state.info = 'watched'
                                        else:
                                            eps = film['Current Episode']
                                            st.session_state.info = 'watched'
                                        st.session_state.eps = int(eps)
                                        st.session_state.edit_eps = True
                                        st.rerun()
                            else:
                                with st.container(width=30):
                                    st.markdown(
                                        f"""
                                        <div style="
                                            display: flex;
                                            align-items: center;
                                            height: 40px;
                                            font-size: 16px;
                                        ">
                                            {st.session_state.eps}/{film['Episode']}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                st.button(':red-background[➖]', key='edit-eps1', on_click=set_eps, args=(st.session_state.eps - 1, int(film['Episode'])), type='tertiary')
                                st.button(':green-background[➕]', key='edit-eps2', on_click=set_eps, args=(st.session_state.eps + 1, int(film['Episode'])), type='tertiary')
                            
                    st.markdown('### Playlist')
                    st.info(film['Playlist']) 
            if st.session_state.edit_eps and st.session_state.info != 'complete':    
                with st.container(horizontal=True):
                    save_edited = st.button('✅', width='stretch', key='save_edited_eps')
                            
                    if st.button('❌', width='stretch', key='cancel_edited_eps'):
                        st.session_state.edit_eps = False
                        st.session_state.info = None
                        st.session_state.rec = False
                        st.rerun()
                    
                if save_edited:
                    row = index+2
                    cells = [
                        {"range": f"A{row}", "values": [["Watched"]]},
                        {"range": f"B{row}", "values": [["On Going"]]},
                        {"range": f"F{row}", "values": [[st.session_state.eps]]}
                    ]

                    if film_worksheet().batch_update(cells):
                        df.at[index, 'Status'] = 'Watched'
                        df.at[index, 'Info'] = 'On Going'
                        df.at[index, 'Current Episode'] = st.session_state.eps
                        
                        st.session_state.film_df = values_handling(df,'film')  # Update session state
                        
                        st.toast('✅ Episode Updated!')
                        time.sleep(1)
                        st.session_state.edit_eps = False
                        st.session_state.info = None
                        st.session_state.rec = False
                        st.rerun()


                if st.session_state.info == 'complete':
                    if film['Status'] == 'Recommended':
                        rec_value = True
                    else:
                        rec_value = False
                    if st.checkbox('Recommended', value=rec_value, on_change=set_rec, key='rec_eps'):
                        edited_status = 'Recommended'
                else: 
                    edited_status = 'Watched'
        
            st.markdown('---')
            st.markdown('## Ratings')
            if st.session_state.info != 'complete':
                with st.container(key='star_rating'):
                    if film['Rating'] == '?':
                        st.write('🌑🌑🌑🌑🌑')
                    else:
                        if film['Rating']%1 == 0:
                            st.write('🌕' * int(film["Rating"]) + '🌑' * (5-int(film['Rating'])))
                        else:
                            st.write('🌕' * int(film["Rating"]) + '🌗' + '🌑' * (5-(int(film['Rating'])+1)))
            else:
                edited_rating = st.number_input('Rating', min_value=0.0, max_value=5.0, step=0.5, value=2.5)
                with st.container(key='star_rating'):
                    if edited_rating%1.00 == 0:
                        st.write('🌕' * int(edited_rating) + '🌑' * (5-int(edited_rating)))
                    else:
                        st.write('🌕' * int(edited_rating) + '🌗' + '🌑' * (5-(int(edited_rating)+1)))
                        
            st.markdown('---')
            st.markdown('## Notes')
            if st.session_state.info != 'complete':
                st.warning(film['Note'])
            else:
                if film['Note'] == '--':
                    notes = ''
                else:
                    notes = film['Note']
                edited_note = st.text_area('Note', placeholder='How do you think about the film/series...', value=notes)

                if edited_note == '':
                    edited_note = '--'
                
            if st.session_state.edit_eps and st.session_state.info == 'complete':    
                if st.session_state.info == 'complete':
                    if film['Status'] == 'Recommended':
                        rec_value = True
                    else:
                        rec_value = False
                    if st.checkbox('Recommended', value=rec_value, on_change=set_rec, key='rec_eps'):
                        edited_status = 'Recommended'
                    else:
                        edited_status = 'Watched'
                else: 
                    edited_status = 'Watched'
                with st.container(horizontal=True):
                    save_edited = st.button('✅', width='stretch', key='save_edited_eps')
                            
                    if st.button('❌', width='stretch', key='cancel_edited_eps'):
                        st.session_state.edit_eps = False
                        st.session_state.info = None
                        st.session_state.rec = False

                        st.rerun()

                    if save_edited:
                        row = index+2
                        cells = [
                            {"range": f"A{row}", "values": [[edited_status]]},
                            {"range": f"B{row}", "values": [["Complete"]]},
                            {"range": f"F{row}", "values": [[st.session_state.eps]]},
                            {"range": f"I{row}", "values": [[edited_rating]]},
                            {"range": f"L{row}", "values": [[edited_note]]}
                        ]

                        if film_worksheet().batch_update(cells):
                            df.at[index, 'Status'] = edited_status
                            df.at[index, 'Info'] = 'Complete'
                            df.at[index, 'Current Episode'] = st.session_state.eps
                            df.at[index, 'Rating'] = edited_rating
                            df.at[index, 'Note'] = edited_note
                            
                            st.session_state.film_df = values_handling(df,'film')  # Update session state
                            
                            st.toast('✅ Episode Updated!')
                            time.sleep(1)
                            st.session_state.edit_eps = False
                            st.session_state.info = None
                            st.session_state.rec = False
                            st.rerun()

        with tab_other_cast:
            try:
                # st.write('Under Construction')
                if film['Cast Name'] != '--':
                    other_casts = film['Cast Name'].split(' ## ')
                    other_cast_main = []
                    other_cast_support = []
                    other_cast_guest = []
                    other_cast_cameo = []
                    for cast in other_casts:
                        cast_data = cast.split('_ ')
                        cast_link = cast_data[0]
                        cast_role = cast_data[1]
                        cast_part = cast_data[2]
                        cast_data = cast_df[cast_df['Link'] == cast_link]
                        if cast_data['Target Name'].iloc[0] != '--':
                            cast_name = cast_data['Target Name'].iloc[0]
                        else:
                            cast_name = cast_data['Name'].iloc[0]
                        if cast_name not in actress_list:
                            cast_img = cast_df[cast_df['Link'] == cast_link]
                            cast_pic = cast_img['Picture'].iloc[0]
                            if cast_part.lower() == 'main role':
                                other_cast_main.append({
                                    'Picture' : cast_pic,
                                    'Name' : cast_name,
                                    'Role' : cast_role,
                                    'Part' : cast_part
                                })
                            elif cast_part.lower() == 'support role':
                                other_cast_support.append({
                                    'Picture' : cast_pic,
                                    'Name' : cast_name,
                                    'Role' : cast_role,
                                    'Part' : cast_part
                                })
                            elif cast_part.lower() == 'guest role':
                                other_cast_guest.append({
                                    'Picture' : cast_pic,
                                    'Name' : cast_name,
                                    'Role' : cast_role,
                                    'Part' : cast_part
                                })
                            elif cast_part.lower() == 'cameo':
                                other_cast_cameo.append({
                                    'Picture' : cast_pic,
                                    'Name' : cast_name,
                                    'Role' : cast_role,
                                    'Part' : cast_part
                                })
                    
                    st.markdown(f"<h2 style='text-align: center;'>Other Cast</h2>", unsafe_allow_html=True)
                    st.subheader(':orange-background[Main Role]')
                    if len(other_cast_main) > 0:
                        if not st.session_state.show_more_main:
                            loop = min(3, len(other_cast_main))
                        else:
                            loop = len(other_cast_main)

                        for i in range(loop):
                            if other_cast_main[i]["Name"] in actress_df['Name (Stage)'].values:
                                st.write(f':yellow-background[{i+1}. {other_cast_main[i]["Name"]}] ✅')
                            else:
                                st.write(f':yellow-background[{i+1}. {other_cast_main[i]["Name"]}]')
                            with st.container(horizontal=True):
                                st.image(other_cast_main[i]['Picture'], width=70)
                                with st.container():
                                    st.write(f'Role Name : :gray-background[{other_cast_main[i]["Role"]}]')
                                    st.write(f'Role Part : :gray-background[{other_cast_main[i]["Part"]}]')
                        if not st.session_state.show_more_main and len(other_cast_main) > min(3, len(other_cast_main)):
                            if st.button('Show More 🔽', key='show_more_main'):
                                st.session_state.show_more_main = True
                                st.rerun()
                        elif st.session_state.show_more_main and len(other_cast_main) > min(3, len(other_cast_main)):
                            if st.button('Show Less 🔼', key='show_less_main'):
                                st.session_state.show_more_main = False
                                st.rerun()

                    else:
                        st.write('--')
                    
                    st.markdown('---')
                    st.subheader(':orange-background[Support Role]')
                    if len(other_cast_support) > 0:
                        if not st.session_state.show_more_support:
                            loop = min(3, len(other_cast_support))
                        else:
                            loop = len(other_cast_support)

                        for i in range(loop):
                            if other_cast_support[i]["Name"] in actress_df['Name (Stage)'].values:
                                st.write(f':yellow-background[{i+1}. {other_cast_support[i]["Name"]}] ✅')
                            else:
                                st.write(f':yellow-background[{i+1}. {other_cast_support[i]["Name"]}]')
                            with st.container(horizontal=True):
                                st.image(other_cast_support[i]['Picture'], width=70)
                                with st.container():
                                    st.write(f'Role Name : :gray-background[{other_cast_support[i]["Role"]}]')
                                    st.write(f'Role Part : :gray-background[{other_cast_support[i]["Part"]}]')
                        if not st.session_state.show_more_support and len(other_cast_support) > min(3, len(other_cast_support)):
                            if st.button('Show More 🔽', key='show_more_support'):
                                st.session_state.show_more_support = True
                        elif st.session_state.show_more_support:
                            if st.button('Show Less 🔼', key='show_less_support'):
                                st.session_state.show_more_support = False
                    else:
                        st.write('--')
                    
                    st.markdown('---')
                    st.subheader(':orange-background[Guest Role]')
                    if len(other_cast_guest) > 0:
                        if not st.session_state.show_more_guest:
                            loop = min(3, len(other_cast_guest))
                        else:
                            loop = len(other_cast_guest)

                        for i in range(loop):
                            if other_cast_guest[i]["Name"] in actress_df['Name (Stage)'].values:
                                st.write(f':yellow-background[{i+1}. {other_cast_guest[i]["Name"]}] ✅')
                            else:
                                st.write(f':yellow-background[{i+1}. {other_cast_guest[i]["Name"]}]')
                            with st.container(horizontal=True):
                                st.image(other_cast_guest[i]['Picture'], width=70)
                                with st.container():
                                    st.write(f'Role Name : :gray-background[{other_cast_guest[i]["Role"]}]')
                                    st.write(f'Role Part : :gray-background[{other_cast_guest[i]["Part"]}]')
                        
                        if not st.session_state.show_more_guest and len(other_cast_guest) > min(3, len(other_cast_guest)):
                            if st.button('Show More 🔽', key='show_more_guest'):
                                st.session_state.show_more_guest = True
                                st.rerun()
                        elif st.session_state.show_more_guest and len(other_cast_guest) > min(3, len(other_cast_guest)):
                            if st.button('Show Less 🔼', key='show_less_guest'):
                                st.session_state.show_more_guest = False
                                st.rerun()
                    else:
                        st.write('--')

                    st.markdown('---')
                    st.subheader(':orange-background[Cameo]')
                    if len(other_cast_cameo) > 0:
                        if not st.session_state.show_more_cameo:
                            loop = min(3, len(other_cast_cameo))
                        else:
                            loop = len(other_cast_cameo)

                        for i in range(loop):
                            if other_cast_cameo[i]["Name"] in actress_df['Name (Stage)'].values:
                                st.write(f':yellow-background[{i+1}. {other_cast_cameo[i]["Name"]}] ✅')
                            else:
                                st.write(f':yellow-background[{i+1}. {other_cast_cameo[i]["Name"]}]')
                            with st.container(horizontal=True):
                                st.image(other_cast_cameo[i]['Picture'], width=80)
                                with st.container():
                                    st.write(f'Role Name : :gray-background[{other_cast_cameo[i]["Role"]}]')
                                    st.write(f'Role Part : :gray-background[{other_cast_cameo[i]["Part"]}]')
                        
                        if not st.session_state.show_more_cameo and len(other_cast_cameo) > min(3, len(other_cast_cameo)):
                            if st.button('Show More 🔽', key='show_more_cameo'):
                                st.session_state.show_more_cameo = True
                                st.rerun()
                        elif st.session_state.show_more_cameo and len(other_cast_cameo) > min(3, len(other_cast_cameo)):
                            if st.button('Show Less 🔼', key='show_less_cameo'):
                                st.session_state.show_more_cameo = False
                                st.rerun()
                    else:
                        st.write('--')
                else:
                    st.warning('No Info') 
                st.markdown('---')
            except Exception as e:
                st.write('ℹ️ Error : Update it from Data Bank ℹ️', e)
        with tab_cast_setting:
            st.write('Under Construction')
            if film['Cast Name'] != '--':

                act_part = st.radio('Role Part', options=['Main', 'Guest', 'Support', 'Cameo'], horizontal=True)

                if act_part == 'Main':
                    max_val = len(other_cast_main)
                    role_part_df = pd.DataFrame(other_cast_main)
                elif act_part == 'Support':
                    max_val = len(other_cast_support)
                    role_part_df = pd.DataFrame(other_cast_support)
                elif act_part == 'Guest':
                    max_val = len(other_cast_guest)
                    role_part_df = pd.DataFrame(other_cast_guest)
                else:
                    max_val = len(other_cast_cameo)
                    role_part_df = pd.DataFrame(other_cast_cameo)
                
                if max_val == 0:
                    max_val = 1


                act_no = st.number_input('Actress Index', min_value=1, max_value=max_val)

                if not role_part_df.empty:
                    act_info = role_part_df.iloc[act_no-1]
                    cast_df_selected = cast_df[cast_df['Name'] == act_info['Name']].iloc[0]
                    idx = cast_df[cast_df['Name'] == act_info['Name']].index[0]
                    actress_index = ACTRESS_OPTS.index(cast_df_selected['Target Name']) if cast_df_selected['Target Name'] in ACTRESS_OPTS else 0

                    st.write('Selected Actress:')
                    with st.container(horizontal=True):
                        st.image(act_info['Picture'], width=90)
                        with st.container():
                            st.write(f'Name : {act_info["Name"]}')
                            st.write(f'Role Name : {act_info["Role"]}')
                            st.write(f'Role Part : {act_info["Part"]}')
                    target_name = st.selectbox('Target', options=ACTRESS_OPTS, index=actress_index)
                    
                    st.markdown('---')
                    save_error = None
                    if st.button('Save Target Name', width='stretch'):
                        if target_name != 'No One':
                            row = idx+2
                            if cast_worksheet().update(f'C{row}', target_name):
                                cast_df.at[idx, 'Target Name'] = target_name
                                st.session_state.cast_df = cast_df
                                st.toast('✅ **:yellow[Target Name]** Added Successfully!')
                                time.sleep(.5)
                                st.rerun()
                        else:
                            save_error = '⚠️ Target Name Cannot be "No One"'
                    if st.button('Add Cast', width='stretch'):
                        if target_name != 'No One':
                            row = idx+2
                            if cast_worksheet().update(f'C{row}', target_name):
                                cast_df.at[idx, 'Target Name'] = target_name
                                row = index+2
                                df.at[index, 'Actress Name'] += f'_ {target_name}'
                                df.at[index, 'Roles'] += f' ## {target_name}_ {act_info["Role"]}_ {act_info["Part"]}'
                                new_data = df.iloc[index].values.tolist()
                                if film_worksheet().update(f'A{row}:T{row}', [new_data]):
                                    st.session_state.film_df = df
                                    st.session_state.cast_df = cast_df
                                    st.toast('✅ **:yellow[Cast]** Added Successfully!')
                                    time.sleep(.5)
                                    st.rerun()
                        else:
                            save_error = '⚠️ Target Name Cannot be "No One"'
                    
                    st.markdown('---')
                    if save_error:
                        st.warning(save_error)
                else:
                    st.warning('No Data')
            else:
                st.warning('No Info!')
        with st.container(key='view_film_edit_container_button', horizontal=True):
            if st.button('✏️ Edit', width='stretch'):
                st.session_state.editing_film_index = index
                st.rerun()
            if st.button('❌ Close', width='stretch'):
                st.session_state.editing_film_index = None
                st.session_state.viewing_film_index = None
                st.session_state.edit_eps = False
                st.session_state.info = None
                st.session_state.rec = False
                st.rerun()

    def show_edit_film(index):
        film = df.iloc[index]

        playlist_index = PLAYLIST_OPTS.index(film['Playlist']) if film['Playlist'] in PLAYLIST_OPTS else 0
        info_s_index = INFO_OPTS_S.index(film['Info']) if film['Info'] in INFO_OPTS_S else 0
        info_m_index = INFO_OPTS_M.index(film['Info']) if film['Info'] in INFO_OPTS_M else 0
        type_index = TYPE_OPTS.index(film['Type']) if film['Type'] in TYPE_OPTS else 0

        tab_edit_film, tab_edit_actress_role, tab_action_btn = st.tabs(['Film Info', 'Actress Role', 'Action'])
        with tab_edit_film:
        
            with st.container(horizontal_alignment='center'): 
                st.markdown(f"### ✏️ Editing: {film['Title']}")
                st.image(film['Picture'], width=250)
                if film['Upload Type'] == 'Local':
                    type_idx = 0
                else:
                    type_idx = 1
                pic_up = st.radio('Picture Upload Type', ['Local', 'Internet'], index=type_idx, horizontal=True )

                if pic_up == 'Local':
                    new_pic = st.file_uploader('Change Image', type=['png', 'jpg', 'jpeg', 'webp'], key=f'film_picture_{index}')#
                    if new_pic is not None:
                        try:
                            st.image(new_pic, width=250)
                        except Exception as e:
                            st.error(f'Error: {e}')
                else:
                    new_pic = st.text_input('Image Link', placeholder='Enter your poster link...',key=f'film_picture_link_{index}')
                    if new_pic == '':
                        new_pic = film['Picture']
                    else:
                        try:
                            st.image(new_pic, width=250)
                        except Exception as e:
                            st.error(f'Error: {e}')
            
            st.subheader("Basic Information")

            edited_title = st.text_area('Title', placeholder='Enter film title...', value=film['Title'], key=f'film_title_{index}')

            if pd.notna(film['Synopsis']) and film['Synopsis'] != '⚠️ Synopsis not found!':
                text_synopsis = film['Synopsis']
            else:
                text_synopsis = ''

            edited_synopsis = st.text_area('Synopsis', placeholder='Enter film synopsis...', value=text_synopsis, key=f'film_synopsis_{index}')
            
            if edited_synopsis == '':
                edited_synopsis = '⚠️ Synopsis not found!'
            
            if film['Cast'] != '--':
                actress_list = [
                    j.strip() for j in film['Cast'].split('_ ')
                    if j.strip() in ACTRESS_OPTS
                ]
            else:
                actress_list = [
                    j.strip() for j in film['Actress Name'].split('_ ')
                    if j.strip() in ACTRESS_OPTS
                ]

            selected_actress = st.multiselect(
                'Actress', 
                options = ACTRESS_OPTS, 
                default = actress_list
            )

            edited_actress = "_ ".join(selected_actress)

            selected_genre = st.multiselect(
                'Genre', 
                options = GENRE_OPTS, 
                default = [
                    j.strip() for j in film['Genre'].split(',')
                    if j.strip() in GENRE_OPTS
                ]
            )

            edited_genre = ", ".join(selected_genre)

            edited_type = st.selectbox('Type', options=TYPE_OPTS, index=type_index)

            if edited_type == 'Movie':
                edited_eps = '?'
                edited_info = st.selectbox('Info', options=INFO_OPTS_M, index=info_m_index)
            else:
                if film['Episode'] == '?':
                    eps = 1
                else:
                    eps = int(film['Episode'])
                edited_eps = st.number_input('Episode',min_value=1, value=eps)
                edited_info = st.selectbox('Info', options=INFO_OPTS_S, index=info_s_index)

            if edited_info == 'On Going':
                if film['Current Episode'] == '?':
                    current_eps = 1
                else:
                    current_eps = int(film['Current Episode'])

                edited_current_eps = st.number_input('Current Episode', min_value=1, max_value=int(film['Episode']), value=current_eps)
                edited_rating = '?'
                edited_status = 'Watched'
            elif edited_info == 'Complete':
                edited_current_eps = edited_eps
                if film['Rating'] == '?':
                    edited_rating = st.number_input('Rating', min_value=0.0, max_value=5.0, step=0.5, value=2.5)
                else:
                    edited_rating = st.number_input('Rating', min_value=0.0, max_value=5.0, step=0.5, value=float(film['Rating']))

                with st.container(key='star_rating'):
                    if edited_rating%1.00 == 0:
                        st.write('🌕' * int(edited_rating) + '🌑' * (5-int(edited_rating)))
                    else:
                        st.write('🌕' * int(edited_rating) + '🌗' + '🌑' * (5-(int(edited_rating)+1)))
                edited_status = 'Watched'
            elif edited_info == 'Drop':
                edited_current_eps = '?'
                edited_rating = 0
                edited_status = 'Dissapointing'
            else:
                edited_current_eps = '?'
                edited_rating = '?'
                edited_status = 'Not Watched'
        
                
            edited_playlist = st.selectbox('Playlist', options=PLAYLIST_OPTS, index=playlist_index, key=f'film_playlist_{index}')
            
            if st.checkbox('New Playlist'):
                new_playlist = st.text_input('New Playlist', placeholder='Enter new playlist...', key=f'film_new_playlist_{index}')
                if new_playlist != '' or new_playlist != None:
                    edited_playlist = new_playlist
            
            if film['Status'] == 'Recommended':
                status_toggle = True
            else:
                status_toggle = False

            if st.toggle('Recommended', value=status_toggle):
                edited_status = 'Recommended'
            
            st.markdown('---')

            if film['Note'] == '--':
                notes = ''
            else:
                notes = film['Note']
            edited_note = st.text_area('Note', placeholder='How do you think about the film/series...', value=notes)

            if edited_note == '':
                edited_note = '--'

        with tab_edit_actress_role:
            errors = None
            if selected_actress and edited_title and edited_genre:
                if 'No One' in selected_actress or edited_type == 'TV Show':
                    st.write('✅ All data inputed successfully!')
                    edited_roles = 'Unqualified'
                else:
                    roles_dict = {
                        'Name': [],
                        'Role Name': [],
                        'Role Part': []
                    }
                    role_error = False
                    actress_df = st.session_state.actress_df.copy()
                    selected_actress_data = actress_df[actress_df['Name (Stage)'].isin(selected_actress)]
                    st.write(selected_actress_data)
                    if film['Roles'] != 'Unqualified':
                        roles_is_empty = pd.isna(film['Roles']) or film['Roles'] == '--'
                        if not roles_is_empty:
                            actress_role_data = []
                            roles_data = film['Roles']
                            roles_list = roles_data.split(' ## ')
                            for actress_data in roles_list:
                                actress_role = actress_data.split('_ ')
                                new_row = [
                                    actress_role[0],
                                    actress_role[1],
                                    actress_role[2]
                                ]
                                actress_role_data.append(new_row)
                            
                            actress_role_df = pd.DataFrame(actress_role_data, columns=['Name', 'Role Name', 'Role Part'])

                            for select_act in selected_actress_data['Name (Stage)'].values:
                                if select_act not in actress_role_df['Name'].values:
                                    new_row = [{
                                        'Name' : select_act,
                                        'Role Name' : '--',
                                        'Role Part' : '--'
                                    }]
                                    new_df = pd.DataFrame(new_row)

                                    final_df = pd.concat([actress_role_df, new_df], ignore_index=True)
                                    actress_role_df = final_df

                        else:
                            actress_role_df = pd.DataFrame(columns=['Name', 'Role Name', 'Role Part'])

                    for idx in selected_actress_data.index:
                        data = selected_actress_data.loc[idx]

                        if data['Name (Stage)'] in actress_role_df['Name'].to_list():
                            role_data = actress_role_df[actress_role_df['Name'] == data['Name (Stage)']].iloc[0]
                            if role_data['Role Name'] == '--':
                                role_data['Role Name'] = ''
                            
                            if role_data['Role Part'] == '--':
                                role_data['Role Part'] = 'Select Role Part'

                        with st.container(horizontal=True, width='stretch'):
                            with st.container(width=110):
                                st.image(data['Picture'], width='stretch')
                            with st.container(width='stretch'):
                                with st.container(horizontal=True):
                                    if data['Name (Stage)'] == data['Name (Given)']:
                                        st.write(data['Name (Stage)'])
                                    else:
                                        st.write(f"{data['Name (Stage)']} / {data['Name (Given)']}")
                                roles_dict['Name'].append(data['Name (Stage)'])
                                if data['Name (Stage)'] in actress_role_df['Name'].to_list():
                                    role_name = st.text_input('Role Name:red[*]', placeholder='Name in alphabet...', width='stretch', key=f'role_name_{idx}', value=role_data['Role Name'])
                                else:
                                    role_name = st.text_input('Role Name:red[*]', placeholder='Name in alphabet...', width='stretch', key=f'role_name_{idx}')
                        if data['Name (Stage)'] in actress_role_df['Name'].to_list():
                            if role_data['Role Part'] != '--':
                                role_part_text = role_data['Role Part'].replace('Role','')
                            role_part_index = ROLE_PART_OPTS.index(role_part_text) if role_part_text in ROLE_PART_OPTS else 0
                            role_part = st.selectbox('Role Part:red[*]', options=ROLE_PART_OPTS, key=f'role_part_{idx}', width='stretch', index=role_part_index)
                        else:
                            role_part = st.selectbox('Role Part:red[*]', options=ROLE_PART_OPTS, key=f'role_part_{idx}', width='stretch', index=0)

                        if st.checkbox('No Info', key=f'no_info_{idx}', value=(role_data['Role Name'] == '')):
                            roles_dict['Role Name'].append('--')
                            roles_dict['Role Part'].append('--')
                        elif role_name and role_part != 'Select Role Part':
                            roles_dict['Role Name'].append(role_name)
                            roles_dict['Role Part'].append(role_part)
                        else:
                            role_error = True

                        st.markdown('---')
                    if not role_error:
                        edited_roles = []
                        for act_name, act_role_name, act_role_part in zip(roles_dict['Name'], roles_dict['Role Name'], roles_dict['Role Part']):
                            edited_roles.append(f"{act_name}_ {act_role_name}_ {act_role_part}")
                        edited_roles = ' ## '.join(edited_roles)
                    else:
                        st.warning('⚠️ Fill All The Role Name And Part!')
                        errors = True
            else:
                st.warning('⚠️ Fill Mandatory Fields First! (:red[*])')
                
        with tab_action_btn:
            if not errors:
                with st.container(horizontal=True):
                    if st.button("💾 Save", width='stretch', type="primary", key=f"save_{index}"):
                        join_code = edited_title
                        clean_code = re.sub(r'[^\w]', '', join_code)
                        clean_code = "N" + clean_code

                        old_filename = str(film['Picture']).split('/')[-1]
                        old_public_id = old_filename.split('.')[0]

                        # kalau cuma ganti foto
                        if (new_pic and new_pic != '') and (edited_title == film['Title']):
                            if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                                try:
                                    if "cloudinary" in film['Picture']:
                                        delete_cloudinary_image(old_public_id)
                                except Exception as e:
                                    st.warning(f"Could not delete old image: {e}")
                                    st.stop()
                            if pic_up == 'Local':
                                final_picture_url = upload_to_database(new_pic, clean_code)
                                if not final_picture_url:
                                    st.error("Failed to upload new image")
                                    st.stop()
                            else:
                                final_picture_url = new_pic

                        # kalau ganti foto dan code
                        elif (new_pic and new_pic != '')     and (film['Title'] != edited_title):
                            if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                                try:
                                    if "cloudinary" in film['Picture']:
                                        delete_cloudinary_image(old_public_id)  
                                except Exception as e:
                                    st.warning(f"Could not delete old image: {e}")
                                    st.stop()
                            if pic_up == 'Local':
                                final_picture_url = upload_to_database(new_pic, clean_code)
                                if not final_picture_url:
                                    st.error("Failed to upload new image")
                                    st.stop()
                            else:
                                final_picture_url = new_pic
                        # kalau cuma ganti code
                        elif not new_pic and (film['Title'] != edited_title):
                            if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                                try:
                                    if pic_up == 'Local' and "cloudinary" in film['Picture']:
                                        final_picture_url = rename_cloudinary_image(old_public_id, clean_code)
                                    else:
                                        final_picture_url = new_pic
                                except Exception as e:
                                    st.warning(f'Could not rename old image: {e}')
                                    st.stop()
                        else:
                            final_picture_url = film['Picture']

                        if film['Title'] != edited_title and edited_title in df['Title'].values:
                            st.warning(f'⚠️ Title {edited_title} already exist in database!')
                        else:
                            # Update data di DataFrame
                            edited_row = [
                                edited_status,
                                edited_info,
                                final_picture_url,
                                edited_title,
                                edited_type,
                                edited_current_eps,
                                edited_eps,
                                edited_genre,
                                edited_rating,
                                edited_playlist,
                                edited_actress,
                                edited_note,
                                pic_up,
                                edited_synopsis,
                                edited_roles,
                                film['Year'],
                                film['Aired'],
                                film['Cast'],
                                film['Cast Name'],
                                film['Link']
                            ]

                            df.loc[index] = edited_row

                            st.session_state.film_df = values_handling(df,'film')  # Update session state
                            st.toast("✅ Data edited successfully!")
                            row = index + 2
                            film_worksheet().update(f'A{row}:T{row}', [edited_row])
                            time.sleep(1)

                            st.session_state.editing_film_index = None
                            st.rerun()
                if st.session_state.delete_film == False:
                    if st.button("🗑️ Delete Film", width='stretch', type="secondary", key=f"delete_{index}"):
                        st.session_state.delete_film = True
                        st.rerun()
                else:
                    st.warning('Are you sure want to delete this film?')
                    with st.container(horizontal=True):
                        if st.button('Yes', width='stretch'):
                            st.session_state.delete_film = False
                            delete_film(index)
                        if st.button('No', width='stretch'):
                            st.session_state.delete_film = False
                            st.rerun()
        if st.button('❌ Cancel', width='stretch'):
            st.session_state.editing_film_index = None
            st.rerun()

                
    
    def delete_film(index):
        film = df.loc[index]
        pic_filename = str(film['Picture']).split('/')[-1]
        pic_id = pic_filename.split('.')[0]

        if 'placeholder' not in pic_id and 'cloudinary' in film['Picture']:
            delete_cloudinary_image(pic_id)

        df.drop(index, inplace=True)
        df.reset_index(drop=True, inplace=True)

        
        st.session_state.film_df = values_handling(df,'film') 
        
        film_worksheet().delete_row(int(index)+2)
        st.session_state.editing_film_index = None
        st.session_state.viewing_film_index = None
        st.rerun()

    @st.dialog("➕ Add New Film", width='small')
    def add_new_film():
        if st.session_state.get('film_reset', False):
            st.session_state.film_reset = False
            st.session_state.new_info_s = INFO_OPTS_S[0]
            st.session_state.new_info_m = INFO_OPTS_M[0]
            st.session_state.new_title = ''
            st.session_state.new_actresses = ''
            st.session_state.new_type = TYPE_OPTS[0]
            st.session_state.new_current_eps = 1
            st.session_state.new_episode = 1
            st.session_state.new_genre = ''
            st.session_state.new_rating = 3
            st.session_state.new_playlist = ''
            st.session_state.new_new_playlist = ''
        
        if 'new_film_reset' not in st.session_state:
            st.session_state.new_film_reset = 0
        
        add_information, add_actress_role =  st.tabs(tabs=['Add Information', 'Actress Role'])
        
        with add_information:
            reset_film = st.session_state.new_film_reset

            pic_up = st.radio('Picture Upload Type',['Local', 'Internet'], horizontal=True)

            if pic_up == 'Local':
                new_picture = st.file_uploader('Image', type=['png', 'jpg', 'jpeg', 'webp'], key=f'new_film_picture_{reset_film}')
            
            else:
                new_picture = st.text_input('Image Link', placeholder='Enter your poster link...')

            if not new_picture is None and not new_picture == '':
                with st.container(horizontal_alignment='center'):
                    st.image(new_picture, width=200)
            else:
                new_picture = st.secrets.indicators.PLACEHOLDER_IMG_POSTER

            new_title = st.text_area('Title:red[*]', key='new_title', placeholder='Enter new film title...') 
            new_synopsis = st.text_area('Synopsis', key='new_synopsis', placeholder='Enter new film synopsis...') 

            if new_synopsis == '':
                new_synopsis = '⚠️ Synopsis not found!'
            selected_actress = st.multiselect('Actress:red[*]', key='new_actresses', options=ACTRESS_OPTS)

            if selected_actress:
                new_actress = "_ ".join(selected_actress)
            else:
                new_actress = '?'

            selected_genre = st.multiselect('Genre:red[*]', key='new_genre', options=GENRE_OPTS)
            new_genre = ", ".join(selected_genre)

            new_type = st.selectbox('Type', key='new_type', options=TYPE_OPTS)

            if new_type == 'Movie':
                new_episode = '?'
                new_current_eps = '?'
                new_info = st.selectbox('Info',key='new_info_m', options=INFO_OPTS_M)
            else:
                new_episode = st.number_input('Episode', key='new_episode', min_value=1)
                new_info = st.selectbox('Info', key='new_info_s', options=INFO_OPTS_S)
            

            if new_info == 'On Going':  
                new_current_eps = st.number_input('Current Episode', min_value=1, max_value=new_episode)
                new_rating = '?'
                new_status = 'Watched'
            elif new_info == 'Complete':
                new_current_eps = new_episode
                new_rating = st.number_input('Rating', min_value = 0.0, max_value = 5.0, value=2.5, step=0.5, key='new_rating')
                with st.container(key='star_rating'):
                    if new_rating%1.00 == 0:
                        st.write('🌕' * int(new_rating) + '🌑' * (5-int(new_rating)))
                    else:
                        st.write('🌕' * int(new_rating) + '🌗' + '🌑' * (5-(int(new_rating)+1)))
                new_status = 'Watched'
            elif new_info == 'Want to Watch':
                new_status = 'Not Watched'
                new_current_eps = '?'
                new_rating = '?'
            else:
                new_current_eps = '?'
                new_rating = '?'
                new_status = 'Dissapointing'

            if st.toggle('Recommended'):
                new_status = 'Recommended'
            new_playlist = st.selectbox('Playlist', key='new_playlist', options=PLAYLIST_OPTS)

            if st.checkbox('New Playlist', key='add_new_playlist'):
                new_new_playlist = st.text_input('New Playlist', placeholder='Enter new playlist...', key='add_film_new_playlist')
                if new_new_playlist != '' or new_new_playlist != None:
                    new_playlist = new_new_playlist
            
            new_note = st.text_area('Note', placeholder='How do you think about the film/series...')

            if new_note == '':
                new_note = '--'

        with add_actress_role:
            errors = None
            if selected_actress and new_title and new_genre:
                if 'No One' in selected_actress or new_type == 'TV Show':
                    st.write('✅ All data inputed successfully!')
                    new_roles = 'Unqualified'
                else:
                    roles_dict = {
                        'Name': [],
                        'Role Name': [],
                        'Role Part': []
                    }
                    role_error = False
                    actress_df = st.session_state.actress_df.copy()
                    selected_actress_data = actress_df[actress_df['Name (Given)'].isin(selected_actress)]
                    for idx in selected_actress_data.index:
                        data = selected_actress_data.loc[idx]
                        with st.container(horizontal=True, width='stretch'):
                            with st.container(width=110):
                                st.image(data['Picture'], width='stretch')
                            with st.container(width='stretch'):
                                with st.container(horizontal=True):
                                    st.write(data['Name (Given)'])
                                roles_dict['Name'].append(data['Name (Given)'])
                                role_name = st.text_input('Role Name:red[*]', placeholder='Name in alphabet...', width='stretch', key=f'role_name_{idx}')
                        role_part = st.selectbox('Role Part:red[*]', options=ROLE_PART_OPTS, key=f'role_part_{idx}', width='stretch', index=0)

                        if st.checkbox('No Info', key=f'no_info_{idx}'):
                            roles_dict['Role Name'].append('--')
                            roles_dict['Role Part'].append('--')
                        elif role_name and role_part != 'Select Role Part':
                            roles_dict['Role Name'].append(role_name)
                            roles_dict['Role Part'].append(role_part)
                        else:
                            role_error = True

                        st.markdown('---')
                    if not role_error:
                        new_roles = []
                        for act_name, act_role_name, act_role_part in zip(roles_dict['Name'], roles_dict['Role Name'], roles_dict['Role Part']):
                            new_roles.append(f"{act_name}_ {act_role_name}_ {act_role_part}")
                        new_roles = ' ## '.join(new_roles)
                    else:
                        st.warning('⚠️ Fill All The Role Name And Part!')
                        errors = True
                if not errors:
                    with st.container(key='film_new_button', horizontal=True):
                        if st.button('💾 Add Film', width='stretch'):
                            if new_picture and new_picture != '':
                                join_name = new_title
                                clean_name = re.sub(r'[^\w]', '', join_name)
                                clean_name = "N" + clean_name
                                if pic_up == 'Local':
                                    picture_url = upload_to_database(new_picture, clean_name)
                                else:
                                    picture_url = new_picture
                            else:
                                picture_url = st.secrets.indicators.PLACEHOLDER_IMG_POSTER
                            
                            new_row = [
                                new_status,
                                new_info,
                                picture_url,
                                new_title,
                                new_type,
                                new_current_eps,
                                str(new_episode),
                                new_genre,
                                new_rating,
                                new_playlist,
                                new_actress,
                                new_note,
                                pic_up,
                                new_synopsis,
                                new_roles,
                                '--',
                                '--',
                                '--',
                                '--',
                                '--'
                            ]

                            df = st.session_state.film_df

                            if new_title in df['Title'].values:
                                errors = f'⚠️ "{new_title}" already exist in database'
                            else:
                                new_row_df = pd.DataFrame([new_row], columns=df.columns)
                                df = pd.concat([df,new_row_df], ignore_index=True)
                                st.session_state.film_df = values_handling(df,'film')
                                st.toast("✅ Data added successfully!")
                                film_worksheet().append_row(new_row)
                                time.sleep(1)
                                st.rerun()
                        if st.button('Close', type='primary', width='stretch'):
                            st.rerun()
                    if errors:    
                        st.warning(errors)
            else:
                st.warning('⚠️ Fill Mandatory Fields First! (:red[*])')
                
    with st.sidebar:
        if st.button('⬅️ Back', width='stretch', on_click=reset_page):
            return 'home'
        
        st.markdown('---')
        new_act_error = False
        
        with st.expander('New Actress'):
            if st.session_state.get('reset_actress', False):
                st.session_state.reset_actress = False
                st.session_state.side_actress_input = ''
                st.session_state.side_actress_job = []

            new_actress_input = st.text_input('New Actress Name:red[*]', placeholder='Format : Alphabet, Kanji', key='side_actress_input')
            if new_actress_input:
                try:
                    new_actress_name, new_actress_native = new_actress_input.split(', ')
                    st.write('Name: ', new_actress_name)
                    st.write('Kanji: ', new_actress_native)
                except Exception as e:
                    st.error(f'Error : {e}')
            new_nationality = st.selectbox('Nationality', options=COUNTRY_OPTS, key='side_actress_nationality')

            new_job = st.multiselect(
                "Job:red[*]", 
                options=JOB_OPTS,
                key=f"side_actress_job"
            )
            group_inputs = {}
            idol_error = False
            group_error = False

            if "Idol" in new_job:
                group_inputs["Idol"] = st.text_input(
                    "Idol Group:red[*]",
                    key=f"new_idol_group"
                )
                if st.checkbox('No Info', key='check_idol_group'):
                    idol_error = False
                    group_inputs['Idol'] = '?'
                elif group_inputs['Idol'] == '':
                    idol_error = True
                else:
                    idol_error = False

            if "Ex-Member" in new_job:
                group_inputs["Ex-Member"] = st.text_input(
                    "Former Group:red[*]",
                    key=f"new_ex_member_group"
                )
                if st.checkbox('No Info', key='check_ex_member_group'):
                    group_error = False
                    group_inputs['Ex-Member'] = '?'
                if group_inputs['Ex-Member'] == '':
                    group_error = True
                else:
                    group_error = False 

            if idol_error or group_error or new_actress_input == '' or new_job == []:
                new_act_error = True
            else:
                new_jobs = format_job_with_groups(new_job, group_inputs)
                new_act_error = False
            
            if st.button('Add Actress', width='stretch'):
                if new_actress_input and not new_act_error:
                    # Create new row data
                    new_row = [
                        'Not Watched',
                        st.secrets.indicators.PLACEHOLDER_IMG,
                        new_actress_name,
                        new_actress_native,
                        '?',
                        '?',
                        new_nationality,
                        '? cm',
                        new_jobs,
                        0,
                        '--',
                        '--'
                    ]

                    # Add to DataFrame
                    df_actress = st.session_state.actress_df

                    if new_row[3] in df_actress['Name (Native)'].values:
                        st.warning(f"⚠️ Actress '{new_row[3]}' already exist in database!")
                        st.stop()
                    else:
                        new_row_df = pd.DataFrame([new_row], columns=actress_df.columns)
                        df_actress = pd.concat([df_actress, new_row_df], ignore_index=True)   
                        df_actress = df_actress.sort_values('Name (Given)', key=lambda col: col.str.lower(), ascending=True, ignore_index=True)
                        # Update ke Google Sheets
                        st.session_state.actress_df = values_handling(df_actress,'actress')  # Update session state
                        actress_worksheet().append_row(new_row)
                        st.session_state.reset_actress = True
                        st.rerun()
                else:
                    st.warning('Fill mandatory fields (:red[*])')
                    st.rerun()
        st.markdown('---')
        show_recommend = st.toggle('Recommended', on_change=reset_page, key='show_recommend')
        st.markdown('---')
        show_display_mode = st.radio('Page', options=['Home', 'Data Bank', 'Scrap'], horizontal=True, key='display_radio')
        st.markdown('---')

        if st.button('➕ Add New Film', width='stretch'):
            add_new_film()
        if st.session_state.log_out_btn == False:
            if st.button('🔐 Logout', width='stretch'):
                st.session_state.log_out_btn = True
                st.rerun()
        else:
            st.warning('Are you sure want to logout?')
            with st.container(horizontal=True):
                if st.button('Yes', width='stretch'):
                    st.session_state.log_out_btn = False
                    st.logout()
                    st.logout()
                    return 'login'
                if st.button('No', width='stretch'):
                    st.session_state.log_out_btn = False
                    st.rerun()
        if st.button('⬆️ Back to top', width='stretch'):
            st.session_state.scroll_to_here = True
            st.rerun()
    
    # Main
    st.space('small')
    
    if st.session_state.viewing_film_index is not None or st.session_state.viewing_bank_index != []:
        show_film_details()

    if show_display_mode == 'Home':
        st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Film List</h1>", unsafe_allow_html=True)
        filtered_df = df.copy()

        if show_recommend:
            filtered_df = filtered_df[filtered_df['Status'] == 'Recommended']
        
        filtered_df = filtered_df.sort_values(by='Title', ascending=True)
        
        display_film_grid(filtered_df, actress_df, device)
    elif show_display_mode == 'Data Bank':
        st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Film Bank</h1>", unsafe_allow_html=True)
        display_film_bank(actress_df, drama_df, movie_df, tv_df, device)
    else:
        st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Scrap</h1>", unsafe_allow_html=True)
        scrap_part = st.radio("Scrap Part", options=["Film", "Cast"], horizontal=True)
        if scrap_part == "Film":
            scrap_type = st.radio("Scrap Type", options=["Drama", "Movie", "TV Show"], horizontal=True)
            
        file = st.file_uploader("Upload HTML", type=["html", "txt"])
        if "cast_results" not in st.session_state:
            st.session_state.cast_results = []
        if "film_results" not in st.session_state:
            st.session_state.film_results = []

        cast_results = st.session_state.cast_results
        st.markdown('---')
        show_scrap = st.button("Show", width='stretch')
        st.markdown('---')
        if show_scrap:
            if scrap_part == "Cast":
                cast_scrap_df = pd.DataFrame(cast_results)
                st.write(cast_scrap_df)
                st.write(st.session_state.cast_df)
        if file is not None:
            html_text = file.read().decode("utf-8")
            soup = BeautifulSoup(html_text, "html.parser")

            if scrap_part == "Cast":
                headers = soup.find_all("h3")

                for h3 in headers:
                    if h3.get_text(strip=True) in ["Guest Role", "Support Role", "Main Role", "Cameo"]:
                        ul = h3.find_next("ul")

                        for item in ul.find_all("li"):
                            name_tag = item.select_one("div.p-a-0 > a.text-primary")
                            name = name_tag.get_text(strip=True) if name_tag else "-"
                            profile_link = name_tag["href"]

                            img = item.select_one("img")["src"]
 
                            small_tag = item.select_one("small")
                            a_tag = small_tag.find("a") if small_tag else None
  
                            character = (
                                a_tag["title"] if a_tag and a_tag.has_attr("title")
                                else small_tag["title"] if small_tag and small_tag.has_attr("title")
                                else "-"
                            )
    
                            role = item.select_one("small.text-muted")
                            role_part = role.get_text(strip=True) if role else "-"

                            st.markdown('---')
                            st.write(name)
                            st.write(profile_link)
                            st.image(img, width=80)
                            st.write(character)
                            st.write(role_part)

                            cast_results.append({
                                "name": name,
                                "link": "https://mydramalist.com" + profile_link,
                                "character": character,
                                "role": role_part,
                                "img": img.replace("s.jpg","c.jpg") 
                            })
            else:
                st.write("scrap film")

    if st.button('⬆️ Back to top', width='stretch'):
        st.session_state.scroll_to_top = True
        st.rerun()
    st.markdown("""
    <style>
    /* Responsive design */
    @media (max-width: 768px) {
        .actress-card {
            height: 420px !important;
        }
    }
    
    /* Custom scrollbar untuk container */
    .st-emotion-cache-1jicfl2 {
        scrollbar-width: thin;
        scrollbar-color: #888 #f1f1f1;
    }
    
    /* Better button styling */
    .stButton > button {
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .st-key-star_rating p {
        font-size: 35px !important;        
    }
    /* ================= DESKTOP ================= */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100% !important;
            width: 300px !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
            box-shadow: 2px 0 20px rgba(0,0,0,0.2) !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
    }

    /* ================= MOBILE ================= */
    @media (max-width: 767px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 100vw !important;
            max-width: 100vw !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .stSidebarCollapseButton button {
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 1000000 !important;
            font-size: 24px !important;
            padding: 14px !important;
            background: rgba(0,0,0,0.1) !important;
            border-radius: 50% !important;
        }

        .main .block-container {
            padding: 1rem !important;
        }
    }

    /* ================= OVERLAY ================= */
    .sidebar-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        z-index: 999998;
        backdrop-filter: blur(2px);
    }

    /* Hide default arrow */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>

    <script>
    document.addEventListener('DOMContentLoaded', function () {

        const waitForSidebar = setInterval(() => {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            const closeBtn = sidebar?.querySelector('button[kind="header"]');

            if (sidebar && closeBtn) {
                clearInterval(waitForSidebar);

                /* ===== AUTO CLOSE ON FIRST LOAD ===== */
                if (sidebar.getAttribute('aria-expanded') === 'true') {
                    closeBtn.click();
                }

                /* ===== CREATE OVERLAY ===== */
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                document.body.appendChild(overlay);

                /* ===== OBSERVE SIDEBAR STATE ===== */
                const observer = new MutationObserver(() => {
                    const expanded = sidebar.getAttribute('aria-expanded') === 'true';
                    overlay.style.display = expanded ? 'block' : 'none';
                    document.body.style.overflow = expanded ? 'hidden' : 'auto';
                });

                observer.observe(sidebar, { attributes: true });

                /* ===== CLICK OVERLAY TO CLOSE ===== */
                overlay.addEventListener('click', () => closeBtn.click());

                /* ===== ESC KEY TO CLOSE ===== */
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && overlay.style.display === 'block') {
                        closeBtn.click();
                    }
                });
            }
        }, 100);
    });
    </script>
    """, unsafe_allow_html=True)

def complex_actress(conn, device):

    if 'actress_initial' not in st.session_state:
        st.session_state.actress_initial = False
    if 'film_initial' not in st.session_state:
        st.session_state.film_initial = False
    if 'scroll_to_top' not in st.session_state:
        st.session_state.scroll_to_top = False
    if 'scroll_to_here' not in st.session_state:
        st.session_state.scroll_to_here = False
    if 'display_mode' not in st.session_state:
        st.session_state.display_mode = 'List'
    if 'detail_movie_index' not in st.session_state:
        st.session_state.detail_movie_index = None
    if 'actress_index' not in st.session_state:
        st.session_state.actress_index = None
    if 'delete_actress' not in st.session_state:
        st.session_state.delete_actress = False

    # Fungsi untuk refresh data dari Google Sheets
    def refresh_data(conn):
        """Refresh data dari Google Sheets ke session state"""
        try:
            init_dataframe_actress()
            init_dataframe_film()
        except Exception as e:
            st.error(f"❌ Error refreshing data: {e}")
            st.stop()

    @st.dialog("🎬 Film Details", width='small')
    def show_movie_details():
        index = st.session_state.detail_movie_index
        film = film_df.iloc[index]
        filtered_actress_df = df.copy()

        with st.container(key='poster_code', horizontal_alignment='center'):
            st.markdown(f"<h2 style='text-align: center;'>{film['Title']}</h2>", unsafe_allow_html=True)
            st.image(film['Picture'], width=200)
        
        st.markdown('### Actress')
        actress_list = film['Actress Name'].split(', ')
        matching_actresses = filtered_actress_df[filtered_actress_df['Name (Given)'].isin(actress_list)]
        for i in range(0,len(matching_actresses)):
            with st.container(horizontal=True):
                st.image(matching_actresses['Picture'].iloc[i], width=80)
                with st.container():
                    st.markdown(f"### {matching_actresses['Name (Given)'].iloc[i]}")
                    # st.markdown(f"### {matching_actresses['Name (Given)'].iloc[i]}")
        with st.container(horizontal=True):
            with st.container():
                st.markdown('### Status')
                st.write(film['Status'])

                st.markdown('### Info')
                st.write(film['Info'])

                st.markdown('### Type')
                st.write(film['Type'])
        
            with st.container():
                st.markdown('### Episode')
                st.write(f"{str(film['Current Episode'])}/{str(film['Episode'])}")

                st.markdown('### Genre')
                st.write(film['Genre'])

                st.markdown('### Playlist')
                st.warning(film['Playlist']) 
        if film['Rating'] == '?':
            st_star_rating(label='Rating', maxValue = 5, defaultValue = 0, key = "rating", read_only = True)
        else:
            st_star_rating(label='Rating', maxValue = 5, defaultValue = int(film['Rating']), key = "rating", read_only = True)

        if st.button('❌ Close', width='stretch'):
            st.session_state.film_detail = False
            st.session_state.viewing_index = st.session_state.actress_index
            st.rerun()

    if st.session_state.scroll_to_top:
        scroll_to_here(0,key='top')  # Scroll to the top of the page
        st.session_state.scroll_to_top = False  # Reset the state after scrolling

    # Inisialisasi DataFrame
    if st.session_state.actress_initial == False:
        df = init_dataframe_actress()
    else:
        df = st.session_state.actress_df
    
    if st.session_state.film_initial == False:
        film_df = init_dataframe_film()
    else:
        film_df = st.session_state.film_df

    # Inisialisasi variabel kontrol
    if "editing_index" not in st.session_state:
        st.session_state.editing_index = None
    if "viewing_index" not in st.session_state:
        st.session_state.viewing_index = None
    if "adding_new" not in st.session_state:
        st.session_state.adding_new = False
    if "film_detail" not in st.session_state:
        st.session_state.film_detail = False
    if "check_clicked" not in st.session_state:
        st.session_state.check_clicked = False
    if "actress_image" not in st.session_state:
        st.session_state.actress_image = 0

    def reset_pic():
        st.session_state.actress_image = 0
    
    def set_actress_image(pic, total):
        if pic < total and pic >=0:
            st.session_state.actress_image = pic

    # Fungsi untuk menghitung usia berdasarkan birthdate
    def calculate_age(birthdate_str):
        try:
            if not birthdate_str or pd.isna(birthdate_str):
                return None
                
            # Handle format "30/09/1992"
            if '/' in str(birthdate_str):
                birth_date = datetime.strptime(str(birthdate_str), '%d/%m/%Y')
            else:
                birth_date = datetime.strptime(str(birthdate_str), '%B %d, %Y')
            
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except:
            return None
        
    @st.dialog("🎬 Actress Details", width="medium")
    def show_actress_details():
        index = st.session_state.viewing_index
        
        if index is None or index >= len(df):
            st.warning("No actress selected")
            return
        
        if st.session_state.editing_index == index:
            show_edit_mode(index)
        else:
            show_view_mode(index)

    def show_view_mode(index):
        actress = df.iloc[index]
        
        # Layout utama dengan gambar dan info dasar
        col1, col2 = st.columns([1, 2])
        
        with col1:
            with st.container(horizontal_alignment='center'):
                st.image(actress['Picture'] if pd.notna(actress['Picture']) else "", width=200)
            
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <h3>{actress['Name (Given)']}</h3>
                    <h2>{actress['Name (Native)'] if pd.notna(actress['Name (Native)']) else ''}</h1>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Tombol Edit dan Close
            no_link_btn_mdl = False
            no_link_btn_asian = False
            button_container = st.container(key='view_edit_close', horizontal=True)
            with button_container:
                with st.container():
                    if st.button("✏️ Edit", width='stretch', key=f"edit_btn_{index}"):
                        st.session_state.editing_index = index
                        st.rerun()
                    if actress['AsianWiki'] != '--':
                        st.link_button("AsianWiki",actress['AsianWiki'], width='stretch', type='primary')
                    else:
                        no_link_btn_asian = st.button('AsianWiki', width='stretch', type='primary')
                with st.container():
                    if st.button("❌ Close", width='stretch', key=f"close_{index}"):
                        st.session_state.viewing_index = None
                        st.session_state.editing_index = None
                        st.rerun()
                    if actress['MDL'] != '--':
                        st.link_button("MDL", actress['MDL'], width='stretch', type='primary')
                    else:
                        no_link_btn_mdl = st.button('MDL', width='stretch', type='primary')

            if no_link_btn_asian:
                st.warning('No link found! (AsianWiki)')
            elif no_link_btn_mdl:
                st.warning('No link found! (MDL)')

        with col2:
            # Info dasar dalam metrics
            st.markdown("### Basic Information")
            
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                
                # Age
                age_text = actress['Age'] if pd.notna(actress['Age']) else ""
                if not age_text and pd.notna(actress['Birthdate']):
                    calculated_age = calculate_age(actress['Birthdate'])
                    if calculated_age:
                        age_text = f"{calculated_age}"
                if age_text:
                    if age_text == '?':
                        age_text = '?'
                    else:
                        age_text = int(age_text)
                    st.metric("Age", f"{age_text} years")
                else:
                    st.metric("Age", f"{0} years")
            
                # Birthdate
                if actress['Birthdate'] != '?':
                    birthdate_text = datetime.strptime(str(actress['Birthdate']), '%d/%m/%Y').date().strftime("%b, %d %Y")
                else:
                    birthdate_text = '?'

                st.metric("Birthdate", str(birthdate_text))
            
            with info_col2:
                # Height
                height_text = actress['Height (cm)'] if pd.notna(actress['Height (cm)']) else "N/A"
                st.metric("Height", height_text)
                
                # Size
                nationality_text = actress['Nationality'] if pd.notna(actress['Nationality']) else "N/A"
                st.metric("Nationality", nationality_text)

                # job_text = actress['Job'] if pd.notna(actress['Job']) else "N/A"
                # st.metric("Job", job_text)

            # Review dengan badge warna
            st.markdown("### Review")
            review_text = actress['Review'] if pd.notna(actress['Review']) else "Active"

            if str(review_text).lower() == "watched":
                st.write(f"## 🟢 {review_text}")
            elif str(review_text).lower() == "not watched":
                st.write(f"## 🔴 {review_text}")
            elif str(review_text).lower() == 'goat':
                st.write(f"## 🟣 {review_text}")
            else:
                st.write(f"## ⚪ {review_text}")

        st.markdown("---")
        
        # Measurement dan Physical Info
        st.markdown("### Job Information")
        job_text = actress['Job'] if pd.notna(actress['Job']) else "N/A"
        job_text = job_text.split(',')
        job_text = "\n".join(f"- {job.strip()}" for job in job_text)

        st.warning(job_text)

        st.markdown("---")

        st.markdown("### Movies")
        filtered_film = film_df[film_df['Actress Name'].str.contains(actress['Name (Given)'])]

        if not filtered_film.empty:
            for i in range(0,len(filtered_film)):
                with st.container(horizontal=True, key=f'film_title_{i}'):
                    if st.button(f'📋', key=f'film_details_{i}', width='content'):
                        st.session_state.viewing_index = None
                        st.session_state.editing_index = None
                        st.session_state.detail_movie_index = filtered_film.index[i]
                        st.session_state.film_detail = True
                        st.rerun()

                    with st.container(width='stretch'):
                        st.write(f'{filtered_film["Title"].iloc[i]}')
                film_card_css = f"""
                <style>
                .st-key-film_title_{i} {{
                    background-color: #1D546D;
                    padding: 5px;
                    border-radius: 5px;
                    display: flex;
                    align-items: center;
                }}

                .st-key-film_title_{i} p {{
                    width: 100%;
                    text-align: left;
                }}

                .st-key-film_details_{i} button {{
                    background-color: #3F9AAE;
                    color: white;
                    border-radius: 6px;
                }}
                </style>
                """
                st.markdown(film_card_css, unsafe_allow_html=True)
        else:
            st.info('No Film')
        
        st.markdown("---")

        st.markdown("### Gallery")
        if st.session_state.get('image_reset', False):
            st.session_state.image_reset = False
            st.session_state.add_new_img = ''
            
        error = ''
        with st.container(horizontal=True, vertical_alignment='bottom'):
            add_new_image = st.text_input('New Image', placeholder='Insert actress image link...', key='add_new_img')
            if st.button('Add', width=80):
                img_list = actress['Gallery']
                img_new = ''

                if add_new_image and add_new_image != '':
                    if img_list == '--':
                        img_new = add_new_image
                    else:
                        img_list = img_list.split(', ')
                        img_list.append(add_new_image)
                        img_new = ', '.join(img_list)
                    st.session_state.actress_df.at[index, 'Gallery'] = img_new
                    st.session_state.image_reset = True
                    row = index + 2
                    actress_worksheet().update(f'N{row}', img_new)
                    st.toast('✅ Image added successfully!')
                    time.sleep(.5)
                    st.rerun()
                else:
                    error = 'Input url first!'
        if error:
            st.warning(error)
        if st.checkbox('Show', on_change=reset_pic):
            if actress['Gallery'] != 'No Pics' and actress['Gallery'] != '--':
                if 'actress_image' not in st.session_state:  
                    st.session_state.actress_image = 0
                
                pics = actress['Gallery'].split(', ')
                count = len(pics)

                st.markdown(
                    """
                    <style>
                    div[data-testid="stVerticalBlock"] { padding-top: 0rem; padding-bottom: 0rem; }

                    .img-fit {
                        margin-top: -13px; 
                        padding-top: 0; 
                        display: flex;             /* gunakan flexbox */
                        justify-content: center;   /* horizontal center */
                        align-items: center;       /* vertical center jika container tinggi ditentukan */
                        background-color: #ffffff;
                        border-radius: 5px;
                        margin-bottom: 15px;
                    }

                    .img-fit img {
                        max-width: 100%;
                        height: 400px;
                        width: auto;
                        object-fit: contain;
                        display: none;  /* default hidden semua gambar */
                    }

                    .img-fit img.active {
                        display: block; /* hanya gambar active yang terlihat */
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                # HTML untuk semua gambar, preload semuanya
                img_html = '<div class="img-fit">'
                for i, pic in enumerate(pics):
                    active_class = 'active' if i == st.session_state.actress_image else ''
                    img_html += f'<img src="{pic}" class="{active_class}" id="img_{i}">'
                img_html += '</div>'

                st.markdown(img_html, unsafe_allow_html=True)


                with st.container(horizontal=True):
                    # Tombol navigasi
                    st.button('⬅️ Previous', disabled=(st.session_state.actress_image == 0), args=(st.session_state.actress_image - 1, count), on_click=set_actress_image, width='stretch')
                    st.button('➡️ Next', disabled=(st.session_state.actress_image == count-1), args=(st.session_state.actress_image + 1, count), on_click=set_actress_image, width='stretch')
                if st.button('🗑️ Delete Image', width='stretch'):
                    new_list = []
                    pics = actress['Gallery'].split(', ')
                    for i in range(count):
                        if i != st.session_state.actress_image:
                            new_list.append(pics[i])
                    
                    img_new = ', '.join(new_list)
                    row = index+2
                    if img_new:
                        st.session_state.actress_df.at[index, 'Gallery'] = img_new
                        actress_worksheet().update(f'N{row}', img_new)

                    else:
                        st.session_state.actress_df.at[index, 'Gallery'] = '--'
                        actress_worksheet().update(f'N{row}', '--')
                    st.toast('✅ Image deleted successfully!')
                    time.sleep(.5)
                    st.rerun()
            else:
                st.warning('No Picture Avaiable!')

        if st.button("Close", width='stretch', key=f'cancel_{index}', type='primary'):
            st.session_state.viewing_index = None
            st.session_state.editing_index = None
            st.rerun()

    def show_edit_mode(index):
        index = st.session_state.editing_index
        actress = st.session_state.actress_df.iloc[index]
        st.space('small')
        st.markdown(f"#### ✏️ Editing: {actress['Name (Given)']}")
        
        # Layout columns
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display current image
            with st.container(horizontal_alignment='center'):
                if pd.notna(actress['Picture']) and actress['Picture']:
                    st.image(actress['Picture'], width=200)
                else:
                    st.write("No picture available")
            
            
            # Tombol aksi
            if st.button("← Back to View", width='stretch', key=f"back_{index}"):
                st.session_state.editing_index = None
                st.rerun()
            
            if st.button("Close", width='stretch', key=f"close_{index}"):
                st.session_state.viewing_index = None
                st.session_state.editing_index = None
                st.rerun()
            if st.session_state.delete_actress == False:
                if st.button("🗑️ Delete Actress", width='stretch', type="secondary", key=f"delete_{index}"):
                    st.session_state.delete_actress = True
                    st.rerun()
            else:
                st.warning('Are you sure want to delete this actress?')
                with st.container(horizontal=True):
                    if st.button('Yes', width='stretch'):
                        st.session_state.delete_actress = False 
                        delete_actress(index) 
                    if st.button('No', width='stretch'):
                        st.session_state.delete_actress = False
                        st.rerun()

            # Image uploader
            new_pic = st.file_uploader("Change Image", type=['png', 'jpg', 'jpeg', 'webp'], key=f"uploader_{index}")
        with col2:
            # Basic Information
            review_index = REVIEW_OPTS.index(actress['Review']) if actress['Review'] in REVIEW_OPTS else 0
            country_index = COUNTRY_OPTS.index(actress['Nationality']) if actress['Nationality'] in COUNTRY_OPTS else 0

            with st.container(horizontal_alignment='center'):
                if new_pic is not None:
                    st.markdown('### New Image')
                    st.image(new_pic, width=200)

            st.subheader("Basic Information")

            if actress['AsianWiki'] == '--':
                asianwiki = ''
            else:
                asianwiki = actress['AsianWiki']

            if actress['MDL'] == '--':
                mdl = ''
            else:
                mdl = actress['MDL']

            edited_asianwiki = st.text_input(
                "AsianWiki", 
                value=asianwiki,
                placeholder='Enter AsianWiki...',
                key=f"asianwiki_{index}"
            )

            if edited_asianwiki == '':
                edited_asianwiki = '--'

            edited_mdl = st.text_input(
                "MDL", 
                value=mdl,
                placeholder='Enter MDL...',
                key=f"mdl_{index}"
            )

            if edited_mdl == '':
                edited_mdl = '--'

            edited_review = st.selectbox(
                "Review", 
                options=REVIEW_OPTS,
                index=review_index,
                key=f"review_{index}"
            )
            
            edited_name_given = st.text_input(
                "Name (Given):red[*]", 
                value=actress['Name (Given)'] if pd.notna(actress['Name (Given)']) else "",
                placeholder="Enter given name in alphabet",
                key=f"name_given_{index}"
            )

            if st.checkbox('Stage Name same as Given Name', value=(actress['Name (Given)'] == actress['Name (Stage)'])):
                edited_name_stage = edited_name_given
            else:
                edited_name_stage = st.text_input(
                    "Name (Stage):red[*]", 
                    value=actress['Name (Stage)'] if pd.notna(actress['Name (Stage)']) else "",
                    placeholder="Enter stage name in alphabet",
                    key=f"name_stage_{index}"
                )
            
            edited_native = st.text_input(
                "Name (Native):red[*]", 
                value=actress['Name (Native)'] if pd.notna(actress['Name (Native)']) else "",
                placeholder="Enter name in native",
                key=f"native_{index}"
            )

            # Handle '?' Value
            if actress['Birthdate'] == '?':
                birth_date = date.today()
            else:
                birth_date = datetime.strptime(actress["Birthdate"], "%d/%m/%Y").date()

            # Birthdate
            edited_birthdate = st.date_input(
                "Birthdate",
                value=birth_date,
                key=f"birthdate_{index}",
                min_value=date(1950,1,1)
            )
            if st.checkbox('No Info', value=(actress['Birthdate'] == '?'), key=f'check_birthdate_{index}'):
                edited_birthdate = '?'
                

            if edited_birthdate != '?':
                age = relativedelta(date.today(), edited_birthdate).years
                edited_birthdate = edited_birthdate.strftime('%d/%m/%Y')
            else:
                age = '?'

            with st.container(horizontal=True):
                if edited_birthdate != '?':
                    st.write('DOB : ', datetime.strptime(str(edited_birthdate), '%d/%m/%Y').date().strftime("%b, %d %Y"))
                else:
                    st.write('DOB : ?')
                st.write('Age : ', str(age))

            height = actress['Height (cm)'].replace(' cm','')

            if height == '?':
                height = 130
            
            edited_height = st.number_input(
                "Height (cm)",
                value=int(height),
                key=f"height_{index}",
                min_value=130
            )

            if st.checkbox('No Info', value=(actress['Height (cm)'] == '?'), key='Height Check'):
                edited_height = '?'
            else:
                edited_height = str(edited_height) + ' cm'

        edited_nationality = st.selectbox('Country', options=COUNTRY_OPTS, index=country_index)


        st.markdown("---")
        default_jobs, job_groups = parse_jobs_with_group(actress['Job'])

        st.subheader("Other Information")
        if st.toggle('Favourite',value=(actress['Favourite'] == 1)):
            edited_favourite = 1
        else:
            edited_favourite = 0
            
        # Job
        edited_job = st.multiselect(
            "Job:red[*]", 
            options=JOB_OPTS,
            default=[j for j in default_jobs if j in JOB_OPTS],
            key=f"notes_{index}"
        )

        group_inputs = {}
        job_error = False
        idol_error = False
        group_error = False

        if "Idol" in edited_job:
            group_inputs["Idol"] = st.text_input(
                "Idol Group",
                value=job_groups.get("Idol", ""),
                key=f"idol_group_{index}"
            )
            if st.checkbox('No Info', key='check_idol_group', value=(group_inputs['Idol']=='?')):
                idol_error = False
                group_inputs['Idol'] = '?'
            elif group_inputs['Idol'] == '':
                idol_error = True
            else:
                idol_error = False

        if "Ex-Member" in edited_job:
            group_inputs["Ex-Member"] = st.text_input(
                "Former Group",
                value=job_groups.get("Ex-Member", ""),
                key=f"ex_member_group_{index}"
            )

            if st.checkbox('No Info', key='check_ex_member_group', value=(group_inputs['Ex-Member'] == '?')):
                group_error = False
                group_inputs['Ex-Member'] = '?'
            if group_inputs['Ex-Member'] == '':
                group_error = True
            else:
                group_error = False

        if idol_error or group_error:
            job_error = True
        else:
            edited_jobs = format_job_with_groups(edited_job, group_inputs)
            job_error = False
        
        st.markdown("---")

        st.markdown("### Gallery")
        if st.session_state.get('image_reset', False):
            st.session_state.image_reset = False
            st.session_state.add_new_img = ''

        error = ''
        with st.container(horizontal=True, vertical_alignment='bottom'):
            add_new_image = st.text_input('New Image', placeholder='Insert actress image link...', key='add_new_img')
            if st.button('Add', width=80):
                img_list = actress['Gallery']
                img_new = ''

                if add_new_image and add_new_image != '':
                    if img_list == '--':
                        img_new = add_new_image
                    else:
                        img_list = img_list.split(', ')
                        img_list.append(add_new_image)
                        img_new = ', '.join(img_list)
                    st.session_state.actress_df.at[index, 'Gallery'] = img_new
                    st.session_state.image_reset = True
                    row = index + 2
                    actress_worksheet().update(f'N{row}', img_new)
                    st.toast('✅ Image added successfully!')
                    time.sleep(.5)
                    st.rerun()
                else:
                    error = 'Input url first!'
        if error:
            st.warning(error)

        if st.checkbox('Show', on_change=reset_pic):
            if actress['Gallery'] != 'No Pics' and actress['Gallery'] != '--':
                if 'actress_image' not in st.session_state:  
                    st.session_state.actress_image = 0
                
                pics = actress['Gallery'].split(', ')
                count = len(pics)

                st.markdown(
                    """
                    <style>
                    div[data-testid="stVerticalBlock"] { padding-top: 0rem; padding-bottom: 0rem; }

                    .img-fit {
                        margin-top: -13px; 
                        padding-top: 0; 
                        display: flex;             /* gunakan flexbox */
                        justify-content: center;   /* horizontal center */
                        align-items: center;       /* vertical center jika container tinggi ditentukan */
                        background-color: #ffffff;
                        border-radius: 5px;
                        margin-bottom: 15px;
                    }

                    .img-fit img {
                        max-width: 100%;
                        height: 400px;
                        width: auto;
                        object-fit: contain;
                        display: none;  /* default hidden semua gambar */
                    }

                    .img-fit img.active {
                        display: block; /* hanya gambar active yang terlihat */
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                # HTML untuk semua gambar, preload semuanya
                img_html = '<div class="img-fit">'
                for i, pic in enumerate(pics):
                    active_class = 'active' if i == st.session_state.actress_image else ''
                    img_html += f'<img src="{pic}" class="{active_class}" id="img_{i}">'
                img_html += '</div>'

                st.markdown(img_html, unsafe_allow_html=True)


                with st.container(horizontal=True):
                    # Tombol navigasi
                    st.button('⬅️ Previous', disabled=(st.session_state.actress_image == 0), args=(st.session_state.actress_image - 1, count), on_click=set_actress_image, width='stretch')
                    st.button('➡️ Next', disabled=(st.session_state.actress_image == count-1), args=(st.session_state.actress_image + 1, count), on_click=set_actress_image, width='stretch')
                if st.button('🗑️ Delete Image', width='stretch'):
                    new_list = []
                    pics = actress['Gallery'].split(', ')
                    for i in range(count):
                        if i != st.session_state.actress_image:
                            new_list.append(pics[i])
                    
                    img_new = ', '.join(new_list)
                    row = index+2
                    if img_new:
                        st.session_state.actress_df.at[index, 'Gallery'] = img_new
                        actress_worksheet().update(f'N{row}', img_new)

                    else:
                        st.session_state.actress_df.at[index, 'Gallery'] = '--'
                        actress_worksheet().update(f'N{row}', '--')
                    st.toast('✅ Image deleted successfully!')
                    time.sleep(.5)
                    st.rerun()
            else:
                st.warning('No Picture Avaiable!')
        # Save changes
        if st.button("💾 Save Changes", width='stretch', type="primary", key=f"save_{index}"):
            if edited_name_given and edited_name_stage and edited_native and edited_job and not job_error:
                if edited_name_given == edited_name_stage:
                    final_name = edited_name_given
                    data_name = actress['Name (Stage)']
                else:
                    final_name = edited_name_stage + ' / ' + edited_name_given
                    data_name = actress['Name (Stage)'] + ' / ' + actress['Name (Given)']
                
                if edited_native in df['Name (Native)'].values and edited_native != actress['Name (Native)']:
                    st.warning(f"⚠️ Actress '{edited_native}' already exist in database!")
                    st.stop()
                else:
                    # Generate clean name untuk public_id
                    join_name = final_name
                    clean_name = re.sub(r'[^\w]', '', join_name)
                    clean_name = "N" + clean_name

                    old_filename = str(actress['Picture']).split('/')[-1]
                    old_public_id = old_filename.split('.')[0]
                    final_picture_url = actress['Picture']

                    # kalau cuma ganti foto
                    if new_pic and (final_name == data_name) and not job_error:
                        if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                            try:
                                delete_cloudinary_image(old_public_id)
                            except Exception as e:
                                st.warning(f"Could not delete old image: {e}")
                                st.stop()
                        
                        final_picture_url = upload_to_database(new_pic, clean_name)
                        if not final_picture_url:
                            st.error("Failed to upload new image")
                            st.stop()
                            return
                        st.toast('ℹ️ Changed Photo')
                    # kalau ganti foto dan code
                    elif new_pic and (final_name != data_name) and not job_error:
                        if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                            try:
                                delete_cloudinary_image(old_public_id)
                            except Exception as e:
                                st.warning(f"Could not delete old image: {e}")
                                st.stop()
                        
                        final_picture_url = upload_to_database(new_pic, clean_name)
                        if not final_picture_url:
                            st.error("Failed to upload new image")
                            st.stop()
                        st.toast('ℹ️ Changed Photo and Name')
                    # kalau cuma ganti code
                    elif not new_pic and (final_name != data_name) and not job_error:
                        if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                            try:
                                final_picture_url = rename_cloudinary_image(old_public_id, clean_name)
                            except Exception as e:
                                st.warning(f'Could not rename old image: {e}')
                                st.stop()
                        st.toast('ℹ️ Name')
                    elif job_error:
                        st.error('Fill mandatory fields! (:red[*])')
                        st.write(not job_error)
                        st.stop()

                    edited_row = [
                        edited_review,
                        final_picture_url,
                        edited_name_given,
                        edited_name_stage,
                        edited_native,
                        edited_birthdate,
                        age,
                        edited_nationality,
                        edited_height,
                        edited_jobs,
                        edited_favourite,
                        edited_asianwiki,
                        edited_mdl,
                        st.session_state.actress_df.at[index, 'Gallery']
                    ]
                    
                    row = index + 2
                    if actress_worksheet().update(f'A{row}:N{row}', [edited_row]):
                        df.loc[index] = edited_row

                        st.session_state.actress_df = values_handling(df,'actress')  # Update session state
                        
                        st.toast("✅ Data edited successfully!")
                        time.sleep(1)

                        st.session_state.editing_index = None
                        st.rerun()
            else:
                st.error('Fill mandatory fields first! (:red[*])')
                st.stop()
    
    def delete_actress(index):
        # Hapus data dari DataFrame
        actress = df.loc[index]
        pic_filename = str(actress['Picture']).split('/')[-1]
        pic_id = pic_filename.split('.')[0]

        if 'placeholder' not in pic_id:
            delete_cloudinary_image(pic_id)

        df.drop(index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        

        st.session_state.actress_df = values_handling(df,'actress')  # Update session state
        st.toast("✅ Data deleted successfully!")
        actress_worksheet().delete_row(int(index)+2)
        time.sleep(1)
        
        st.session_state.editing_index = None
        st.session_state.viewing_index = None
        st.rerun()
    
    @st.dialog("➕ Add New Actress", width="large")
    def add_new_actress():
        st.space('small')
        st.markdown("<h3 style='text-align: center; margin-bottom: 15px;'>➕ Add New Actress</h3>", unsafe_allow_html=True)

        if st.session_state.get('reset_flag', False):
            st.session_state.reset_flage = False
            st.session_state.new_review = REVIEW_OPTS[0]
            st.session_state.new_name = ''
            st.session_state.new_native = ''
            st.session_state.new_nationality = COUNTRY_OPTS[0]
            st.session_state.new_birthdate = date.today()
            st.session_state.new_height = 130
            st.session_state.new_job = ''
            st.session_state.new_idol_group = ''
            st.session_state.new_ex_member_group = ''
        
        if 'new_pic_reset' not in st.session_state:
            st.session_state.new_pic_reset = 0
        
        reset_pic = st.session_state.new_pic_reset        
        
        # Basic Information
        new_picture = st.file_uploader("Image", type=['png', 'jpg', 'jpeg', 'webp'], key=f'new_picture_{reset_pic}')
        if new_picture:
            with st.container(horizontal_alignment='center'):
                st.image(new_picture, width=200)    
        st.subheader("Basic Information")
        new_asianwiki = st.text_input("AsianWiki", placeholder='Enter AsianWiki....', key='new_asianwiki')
        if not new_asianwiki:
            new_asianwiki = '--'
        
        new_mdl = st.text_input("MDL", placeholder='Enter MDL....', key='new_mdl')
        if not new_mdl:
            new_mdl = '--'

        new_review = st.selectbox("Review", options=REVIEW_OPTS, key='new_review')
        
        new_name_given = st.text_input("Name (Given):red[*]", placeholder="Enter given name in alphabet", key='new_name_given')
        if st.checkbox('Stage Name same as Given Name', key='new_same_name', value=True):
            new_name_stage = new_name_given
        else:
            new_name_stage = st.text_input("Name (Stage):red[*]", placeholder="Enter stage name in alphabet", key='new_name_stage')

        new_native = st.text_input("Name (Native):red[*]", placeholder="Enter name in native", key='new_native')
        new_nationality = st.selectbox("Country", options=COUNTRY_OPTS, key='new_nationality')
        new_birthdate = st.date_input("Birthdate", min_value=date(1950,1,1), key='new_birthdate')

        if st.checkbox('No Info', key='New Birthdate', value=(new_birthdate is None)):
            new_birthdate = '?'
            new_age = '?'
        elif new_birthdate != '' and new_birthdate != None:
            new_age = relativedelta(date.today(), new_birthdate).years        
            new_birthdate = new_birthdate.strftime('%d/%m/%Y')
            st.write('Birthdate : ', datetime.strptime(str(new_birthdate), '%d/%m/%Y').date().strftime("%b %d, %Y"))
        else:
            new_birthdate = '?'
            new_age = '?'

        st.write('Age : ', str(new_age))

        new_height = st.number_input("Height (cm)", min_value=130, key='new_height')
        if st.checkbox('No Info', key='New Height'):
            new_height = '? cm'
        else:
            new_height = str(new_height) + ' cm'

        new_job = st.multiselect(
            "Job:red[*]", 
            options=JOB_OPTS,
            key=f"new_job"
        )
        group_inputs = {}
        job_error = False
        idol_error = False
        group_error = False

        if "Idol" in new_job:
            group_inputs["Idol"] = st.text_input(
                "Idol Group",
                key=f"new_idol_group"
            )
            if st.checkbox('No Info', key='check_idol_group'):
                idol_error = False
                group_inputs['Idol'] = '?'
            elif group_inputs['Idol'] == '':
                idol_error = True
            else:
                idol_error = False

        if "Ex-Member" in new_job:
            group_inputs["Ex-Member"] = st.text_input(
                "Former Group",
                key=f"new_ex_member_group"
            )
            if st.checkbox('No Info', key='check_ex_member_group'):
                group_error = False
                group_inputs['Ex-Member'] = '?'
            if group_inputs['Ex-Member'] == '':
                group_error = True
            else:
                group_error = False 

        if idol_error or group_error:
            job_error = True
        else:
            new_jobs = format_job_with_groups(new_job, group_inputs)
            job_error = False

        st.subheader("Other Information")
        if st.toggle('Favourite'):
            new_favourite = 1
        else:
            new_favourite = 0

        st.space('small')

        # Tombol submit
        with st.container(horizontal=True):
            submit_new = st.button("💾 Add Actress", width='stretch')
            cancel_new = st.button("❌ Cancel", width='stretch')
        
        if submit_new:
            if new_name_given and new_name_stage and new_native and new_job and not job_error:
                if new_picture:
                    if new_name_given == new_name_stage:
                        join_name = new_name_given
                    else:
                        join_name = new_name_stage + ' / ' + new_name_given
                    clean_name = re.sub(r'[^\w]', '', join_name)
                    clean_name = "N" + clean_name
                    picture_url = upload_to_database(new_picture, clean_name)
                else:
                    picture_url = st.secrets.indicators.PLACEHOLDER_IMG

                # Create new row data
                new_row = [
                    new_review,
                    picture_url,
                    new_name_given,
                    new_name_stage,
                    new_native,
                    new_birthdate,
                    new_age,
                    new_nationality,
                    new_height,
                    new_jobs,
                    new_favourite,
                    new_asianwiki,
                    new_mdl,
                    '--'
                ]

                # Add to DataFrame
                df = st.session_state.actress_df


                if new_native in df['Name (Native)'].values:
                    st.warning(f"⚠️ Actress '{new_native}' already exist in database!")
                    st.stop()
                else:
                    if actress_worksheet().append_row(new_row):
                        new_row_df = pd.DataFrame([new_row], columns=df.columns)
                        df = pd.concat([df, new_row_df], ignore_index=True)       

                        st.session_state.actress_df = values_handling(df,'actress')  # Update session state
                        st.toast("✅ Data added successfully!")
                        time.sleep(1)                    
                        st.session_state.adding_new = False
                        st.rerun()
            else:
                st.error('Fill mandatory fields first! (:red[*])') # Error disini
                st.stop()
        
        if cancel_new:
            st.session_state.adding_new = False
            st.rerun()

    # Sidebar
    with st.sidebar:
        if st.button('⬅️ Back', width='stretch', on_click=reset_page_actress):
            return 'home'
        st.header(f'Actress Listed : {len(st.session_state.actress_df)}')
        st.markdown("---")
        st.header("⚙️ Display Settings")
        st.session_state.display_mode = st.radio(
            "View Mode",
            ["Gallery", "List"],
            key='display_mode_radio',
            index=0 if st.session_state.display_mode == "Gallery" else 1,
            on_change=reset_page_actress
        )
        st.markdown("---")
        with st.container(key='review_filter'):
            st.header("Review Filters")
            show_actress_watched = st.checkbox("Watched", value=True, on_change=reset_page_actress)
            show_actress_not_watched = st.checkbox("Not Watched", value=True, on_change=reset_page_actress)
        with st.container(key='Favourite'):
            st.header("Favourite Filters")
            show_favourite = st.checkbox("Favourite",value=False, on_change=reset_page_actress)
        
        st.markdown("---")
        st.subheader("Management")
        if st.button("➕ Add New Actress", width='stretch', on_click=reset_page_actress):
            st.session_state.adding_new = True
            st.rerun()
        
        # Tombol refresh data
        if st.button("🔄 Refresh Data", width='stretch'):
            refresh_data(conn)
        
        if st.session_state.log_out_btn == False:
            if st.button('🔐 Logout', width='stretch'):
                st.session_state.log_out_btn = True
                st.rerun()
        else:
            st.warning('Are you sure want to logout?')
            with st.container(horizontal=True):
                if st.button('Yes', width='stretch', on_click=reset_page_actress):
                    st.session_state.log_out_btn = False
                    st.logout()
                    return 'login'
                if st.button('No', width='stretch'):
                    st.session_state.log_out_btn = False
                    st.rerun()
    if st.session_state.adding_new:
        add_new_actress()

    if st.session_state.viewing_index is not None:
        show_actress_details()

    if st.session_state.film_detail:
        show_movie_details()
    
    COUNTRY_FILTER = ['All'] + sorted(
        df.loc[df['Nationality'] != 'All', 'Nationality']
        .dropna()
        .unique()
        .tolist()
    )

    if not df.empty and 'Picture' in df.columns:
        if st.session_state.get('search_reset', False):
            st.session_state.search_reset = False
            st.session_state.search_bar = ''
            st.session_state.check_country = 'All'
        

        search_container = st.container(horizontal=True, vertical_alignment='bottom')

        with search_container:
            search_query = st.text_input("🔍 Search actress by Name (Alphabet / Kanji):", 
                            placeholder="Type name to search...", key='search_bar', on_change=reset_page_actress)
            if st.button('Clear', on_click=reset_page_actress):
                st.session_state.search_reset = True
                st.rerun()
            
        country = st.selectbox('Country', options=COUNTRY_FILTER, key='check_country', on_change=reset_page_actress)
        a_z_filter = st.selectbox('Filter by Name (A–Z)', options=['All'] + list(string.ascii_uppercase), on_change=reset_page_actress)

        # Filter DataFrame berdasarkan status
        filtered_df = df.copy()
        filtered_df = filtered_df.sort_values(by='Name (Given)', ascending=True)

        # Buat kondisi filter
        review_conditions = []
        if show_actress_watched:
            review_conditions.append(filtered_df['Review'].str.lower() == 'watched')
        if show_actress_not_watched:
            review_conditions.append(filtered_df['Review'].str.lower() == 'not watched')
        
        favourite_conditions = []
        if show_favourite:
            favourite_conditions.append(filtered_df['Favourite'] == 1.0)
        else:
            favourite_conditions.append(filtered_df['Favourite'] == 0.0)
            favourite_conditions.append(filtered_df['Favourite'] == 1.0)


        if review_conditions:
            review_mask = review_conditions[0]
            for cond in review_conditions[1:]:
                review_mask |= cond
        else:
            review_mask = pd.Series(False, index=filtered_df.index)
        
        if favourite_conditions:
            favourite_mask = favourite_conditions[0]
            for cond in favourite_conditions[1:]:
                favourite_mask |= cond
        else:
            favourite_mask = pd.Series(False, index=filtered_df.index)
        
        final_mask = review_mask & favourite_mask
        filtered_df = filtered_df[final_mask]
        if country != 'All':
            filtered_df = filtered_df[filtered_df['Nationality'] == country] 

        if a_z_filter != 'All':
            filtered_df = filtered_df[filtered_df['Name (Given)'].str.startswith(a_z_filter)] 

        if search_query and not search_query.isspace() and not filtered_df.empty:
            search_lower = search_query.lower().strip()
            search_mask = (
                filtered_df['Name (Given)'].fillna('').str.lower().str.contains(search_lower, na=False) |
                filtered_df['Name (Native)'].fillna('').str.contains(search_query.strip(), na=False)
            )
            filtered_df = filtered_df[search_mask]

        total_actress_pages = max(1, (len(filtered_df) + 30 - 1) // 30)
        if st.session_state.scroll_to_here:
            scroll_to_here(0,key='here')  # Scroll to the top of the page
            st.session_state.scroll_to_here = False
        st.markdown('---')
        if 'actress_page' not in st.session_state:
            st.session_state.actress_page = 1

        def set_page(p):
            st.session_state.actress_page = p
        st.markdown(
            f"<div style='text-align:center; font-weight:600;padding-bottom:15px'>Page {st.session_state.actress_page}</div>",
            unsafe_allow_html=True
        )

        if total_actress_pages <= 6:
            with st.container(key='page_button', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_actress_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_top', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_top', disabled=(st.session_state.actress_page == 1), on_click=set_page, args=(st.session_state.actress_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
                start_page = max(1, st.session_state.actress_page - 1)  
                end_page = min(total_actress_pages, st.session_state.actress_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_actress_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_actress_pages - 3), total_actress_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_top_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_top', disabled=(st.session_state.actress_page == total_actress_pages), on_click=set_page, args=(st.session_state.actress_page+1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
            with st.container(horizontal=True):
                if st.button('⏮️ First Page', key='first_top', disabled=(st.session_state.actress_page == 1), on_click=set_page, args=(1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page ⏭️', key='last_top', disabled=(st.session_state.actress_page == total_actress_pages), on_click=set_page, args=(total_actress_pages,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
        
        page = st.session_state.actress_page
        
        start_idx = (page - 1) * 30 # page = 2 / Start idx = 8
        end_idx = min(start_idx + 30, len(filtered_df)) # end idx = 16
        
        st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} films")
        
        rows_to_display = filtered_df.iloc[start_idx:end_idx] #[8,15]
        if search_query and not search_query.isspace() and not filtered_df.empty:
            st.info(f'Showing {len(filtered_df)} results')
        elif search_query and not search_query.isspace() and filtered_df.empty:
            st.warning("No actresses match the selected filters.")

        if st.session_state.display_mode == "Gallery":
            try:
                if device == 'Device 1':
                    img_width = 110
                else:
                    img_width = 101
                with st.container(horizontal=True):
                    for idx in rows_to_display.index:
                        actress = df.iloc[idx]
                        with st.container(width=img_width+5):
                            st.markdown(f"""
                                <div style="
                                width: {img_width}px;
                                height: {img_width}px;
                                border-radius: 50%;
                                overflow: hidden;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                margin: 0 auto 8px auto;
                                background: white;
                                border: 2px solid #374151;
                            ">
                                <img src="{actress['Picture']}" 
                                    style="
                                        width: 100%;
                                        height: 100%;
                                        object-fit: cover;
                                    ">
                            </div>
                            """, unsafe_allow_html=True)
                            if actress['Name (Given)'] == actress['Name (Stage)']:
                                if st.button(f":gray-background[{actress['Name (Given)']}]", width='stretch', type='tertiary', key=f"{actress['Name (Given)']}_{idx}"):
                                    st.session_state.viewing_index = idx
                                    st.session_state.editing_index = None
                                    st.rerun()
                            else:
                                if st.button(f":gray-background[{actress['Name (Given)']} ({actress['Name (Stage)']})]", width='stretch', type='tertiary', key=f"{actress['Name (Given)']}_{idx}"):
                                    st.session_state.viewing_index = idx
                                    st.session_state.editing_index = None
                                    st.rerun()
            except Exception as e:
                st.error(f'Error Generate Image: {e}')
                st.stop()
        else:
            with st.container(horizontal=True, horizontal_alignment='center'):
                for i in range(0,len(rows_to_display)):
                    index = rows_to_display.index[i]
                    review_text = rows_to_display['Review'].iloc[i]
                    if rows_to_display['Name (Stage)'].iloc[i] == rows_to_display['Name (Given)'].iloc[i]:
                        name = rows_to_display['Name (Given)'].iloc[i]
                    else:
                        name = rows_to_display['Name (Stage)'].iloc[i] + ' / ' + rows_to_display['Name (Given)'].iloc[i]

                    if review_text == 'Not Watched':
                        review_icon = '🔴'
                        review_color = 'red'
                    elif review_text == 'Watched':
                        review_icon = '🟢'
                        review_color = 'green'
                    else:
                        review_icon = '⚪'
                        review_color = 'grey'
                    with st.container(key=f'actress_card_{i}', width=570):
                        with st.container(horizontal=True, horizontal_alignment='distribute'):
                            with st.container(width='content'):
                                st.markdown(f"""
                                <div style="line-height: 1; margin-bottom: 10px;">
                                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 10px;">
                                        {name[:23] + "..." if len(name) > 23 else name}
                                    </div>
                                    <div style="font-size: 0.8rem; color: #d7dae0; margin-top: 0;">
                                        {rows_to_display["Name (Native)"].iloc[i]}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            with st.container(horizontal_alignment='right', horizontal=True, width='content'):
                                st.badge(f"{rows_to_display['Review'].iloc[i]}",icon=review_icon, color=review_color)
                                if rows_to_display['Favourite'].iloc[i] == 1:
                                    st.badge(f"",icon='⭐', color='yellow',width='content')
                        with st.container(horizontal=True,width='content'):
                            st.markdown(f"""
                                <div style="
                                    width: 120px;
                                    height: 120px;
                                    border-radius: 50%;
                                    overflow: hidden;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    background: white;
                                    border: 2px solid #374151;    
                                ">
                                    <img src="{rows_to_display['Picture'].iloc[i]}" 
                                        style="
                                            width: 100%;
                                            height: 100%;
                                            object-fit: cover;
                                        ">
                                </div>
                            """, unsafe_allow_html=True)
                            with st.container(horizontal=False, width='content'):
                                if rows_to_display['Birthdate'].iloc[i] == '?':
                                    st.write('🎂 DoB : ?')
                                else:
                                    st.write(f'🎂 DoB : {datetime.strptime(rows_to_display["Birthdate"].iloc[i],"%d/%m/%Y").date().strftime("%b %d, %Y")}')
                                st.write(f'👧 Age : {rows_to_display["Age"].iloc[i]}')
                                st.write(f'🌍 Country : {rows_to_display["Nationality"].iloc[i]}')
                        if st.button('🔍 View Details', key=f"button_{rows_to_display['Name (Given)'].iloc[i]}_{rows_to_display['Name (Stage)'].iloc[i]}", width='stretch'):
                            st.session_state.viewing_index = index
                            st.session_state.editing_index = None
                            st.session_state.actress_index = index

                            show_actress_details()
                            st.rerun()
                        st.markdown(f"""
                            <style>
                                .st-key-actress_card_{i}{{
                                    background-color: #1D546D;
                                    padding:10px 10px 1px 10px;
                                    border-radius: 5px;
                                }}
                            </style>
                        """, unsafe_allow_html=True)
                    st.space('small')
            
        st.markdown('---')
        if total_actress_pages <= 6:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                for i in range(1, total_actress_pages + 1):
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
        else:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_bottom', disabled=(st.session_state.actress_page == 1), on_click=set_page, args=(st.session_state.actress_page-1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
                start_page = max(1, st.session_state.actress_page - 1)  
                end_page = min(total_actress_pages, st.session_state.actress_page + 2)  
                
                pages_to_show = range(start_page, end_page + 1)
                
                if len(pages_to_show) < 4:
                    if start_page == 1:
                        pages_to_show = range(1, min(5, total_actress_pages + 1))
                    else:
                        pages_to_show = range(max(1, total_actress_pages - 3), total_actress_pages + 1)
                
                for i in pages_to_show:
                    if st.button(
                        str(i),
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.actress_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                        st.rerun()
                
                if st.button('➡️',key='next_bottom', disabled=(st.session_state.actress_page == total_actress_pages), on_click=set_page, args=(st.session_state.actress_page+1,)):
                    st.session_state.scroll_to_here = True    
                    st.rerun()
            with st.container(horizontal=True):
                if st.button('⏮️ First Page', key='first_top', disabled=(st.session_state.actress_page == 1), on_click=set_page, args=(1,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                if st.button('Last Page ⏭️', key='last_top', disabled=(st.session_state.actress_page == total_actress_pages), on_click=set_page, args=(total_actress_pages,)):
                    st.session_state.scroll_to_here = True
                    st.rerun()
                
    else:
        st.info("No actress data available. Click 'Add New Actress' to get started!")
        
    st.markdown("""
    <style>
    /* ================= DESKTOP ================= */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100% !important;
            width: 400px !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
            box-shadow: 2px 0 20px rgba(0,0,0,0.2) !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
    }

    /* ================= MOBILE ================= */
    @media (max-width: 767px) {
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 100vw !important;
            max-width: 100vw !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease-in-out;
            z-index: 999999 !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0) !important;
        }

        .stSidebarCollapseButton button {
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 1000000 !important;
            font-size: 24px !important;
            padding: 14px !important;
            background: rgba(0,0,0,0.1) !important;
            border-radius: 50% !important;
        }

        .main .block-container {
            padding: 1rem !important;
        }
    }

    /* ================= OVERLAY ================= */
    .sidebar-overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        z-index: 999998;
        backdrop-filter: blur(2px);
    }

    /* Hide default arrow */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>

    <script>
    document.addEventListener('DOMContentLoaded', function () {

        const waitForSidebar = setInterval(() => {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            const closeBtn = sidebar?.querySelector('button[kind="header"]');

            if (sidebar && closeBtn) {
                clearInterval(waitForSidebar);

                /* ===== AUTO CLOSE ON FIRST LOAD ===== */
                if (sidebar.getAttribute('aria-expanded') === 'true') {
                    closeBtn.click();
                }

                /* ===== CREATE OVERLAY ===== */
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                document.body.appendChild(overlay);

                /* ===== OBSERVE SIDEBAR STATE ===== */
                const observer = new MutationObserver(() => {
                    const expanded = sidebar.getAttribute('aria-expanded') === 'true';
                    overlay.style.display = expanded ? 'block' : 'none';
                    document.body.style.overflow = expanded ? 'hidden' : 'auto';
                });

                observer.observe(sidebar, { attributes: true });

                /* ===== CLICK OVERLAY TO CLOSE ===== */
                overlay.addEventListener('click', () => closeBtn.click());

                /* ===== ESC KEY TO CLOSE ===== */
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && overlay.style.display === 'block') {
                        closeBtn.click();
                    }
                });
            }
        }, 100);
    });
    </script>
    """, unsafe_allow_html=True)

    # CSS untuk styling card yang estetik
    st.markdown("""
    <style>
        /* Container untuk beberapa badge */
        .badge-stack {
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            gap: 6px;
            z-index: 10;
        }

        /* Status badge (yang sudah ada) */
        .status-badge {
            padding: 4px 9px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
            text-align: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }

        /* Review badge */
        .review-badge {
            padding: 4px 9px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            text-align: center;
            color: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }

        /* Warna review */
        .review-watched { background-color: #2ecc71; }
        .review-goat { background-color: #9b59b6; }
        .review-not-watched { background-color: #e74c3c; }

        /* Supaya badge nempel di card */
        .cat-card {
            position: relative;
        }

        .cat-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 20px 15px;
            margin: 10px;
            border-radius: 15px;
            border: 2px solid #e0e0e0;
            background: linear-gradient(135deg, #F5E5E1 0%, #f8f9fa 100%);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            min-height: 280px;
            width: 100%;
            max-width: 220px;
            cursor: pointer;
        }
        .cat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            border-color: #ff6b6b;
        }
        .cat-image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 15px;
            width: 130px;
            height: 130px;
            overflow: hidden;
            border-radius: 10px;
            background: linear-gradient(135deg, #F5E5E1 0%, #f8f9fa 100%);
        }
        .cat-image {
            border-radius: 10px;
            object-fit: cover;
            max-width: 130px;
            max-height: 130px;
            border: 2px solid #ff6b6b;
        }
        .cat-name {
            font-weight: 700;
            font-size: 16px;
            color: #2c3e50;
            margin: 5px 0;
            line-height: 1.3;
        }
        .cat-kanji {
            font-size: 18px;
            color: #e74c3c;
            margin: 5px 0;
            font-weight: 500;
            line-height: 1.3;
        }
        .card-divider {
            width: 50px;
            height: 2px;
            background: linear-gradient(90deg, #ff6b6b, #ffa726);
            margin: 8px 0;
            border-radius: 2px;
        }
        .card-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 5px;
            width: 100%;
        }
        .button-container {
            display: flex;
            gap: 5px;
            margin-top: 10px;
            width: 100%;
        }
        .button-container button {
            flex: 1;
        }
    </style>
    """, unsafe_allow_html=True)


st.markdown("""
<style>
    ul[data-testid="stSelectboxVirtualDropdown"] li:nth-child(odd){
        background-color:#202124 !important;
    }

    ul[data-testid="stSelectboxVirtualDropdown"] li:nth-child(even){
        background-color:#2d2f31 !important;
    }
</style>
""", unsafe_allow_html=True)
