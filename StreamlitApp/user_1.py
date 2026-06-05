import streamlit as st
from datetime import datetime, date
import time
import re
from upload_image import upload_to_database, delete_cloudinary_image, rename_cloudinary_image
import pandas as pd
from value_handling import values_handling
from dateutil.relativedelta import relativedelta
from streamlit_scroll_to_top import scroll_to_here
import gspread
from google.oauth2.service_account import Credentials
import string
from bs4 import BeautifulSoup
from streamlit_float import *

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
    "Indonesian",
    "South Korean",
    "Japanese",
    "Chinese",
    "Taiwanese",
    "Hong Kong",
    "Thai",
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
    "[PLACEHOLDER]",
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

    ACTRESS_OPTS = ['All', 'No One'] + sorted(
        actress_df.loc[actress_df['Name (Stage)'] != 'No One', 'Name (Stage)']
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
        st.session_state.search_actress = 'All'
        st.session_state.search_text = ''
        
    if st.session_state.get('set_search', False):
        st.session_state.set_search = False
        st.session_state.filter_mode = 'Name'
        st.session_state.search_actress = st.session_state.search_text
        st.session_state.search_text = ''

    with st.sidebar:
        filter_mode = st.radio('Search By:', options=['Title', 'Name'], horizontal=True, key='filter_mode')
        with st.container(horizontal=True, vertical_alignment='bottom'):
            if filter_mode == 'Title':
                search_name = st.text_input("🔍 Search (Title):", placeholder="Enter Movie or Series...", key='search_bar', on_change=reset_page)
                if st.button('Clear', on_click=reset_page):
                    st.session_state.search_reset = True
                    st.rerun()
            else:
                search_name = st.selectbox('Actress Name', options=ACTRESS_OPTS, key='search_actress')
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
        if filter_mode == 'Title':
            mask = filtered_df['Title'].str.contains(search_name, case=False, na=False)
            filtered_df = filtered_df[mask]
        elif filter_mode == 'Name' and search_name != 'All':
            mask = filtered_df['Actress Name'].str.contains(search_name, case=False, na=False)
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
                        title_background_color = '826C22'
                    else:
                        title_background_color = '374151'

                    
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
                                border: 1px solid #{title_background_color}; 
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
                        if st.button(f':gray-background[{title}]', key=f'film_detail_btn_{real_index}', width='stretch', type='tertiary'):
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
    
@st.dialog('Film Scrap', width='small')
def display_scrap_manual(): #scrapping
    df = init_dataframe_film()
    actress_df = init_dataframe_actress()

    TITLE_OPTS = ['New'] + sorted(
        df.loc[df['Title'] != 'All', 'Title']
        .dropna()
        .unique()
        .tolist()
    )

    if st.session_state.get('html_reset', False):
        st.session_state.html_reset = False
        st.session_state.html_bar = ''

    file = st.text_area("HTML TEXT", placeholder="Paste your html here...", key='html_bar')
    if st.button('Clear HTML', width='stretch', type='primary'):
        st.session_state.html_reset = True
        st.rerun()

    if file:
        soup = BeautifulSoup(file, "html.parser")
        html_link = soup.find("link", rel="canonical")
        s_part = html_link.get("href") if html_link else '--'
        s_part = s_part.strip()

        if '/cast' in s_part:
            scrap_part = 'Cast'
        elif '/people' in s_part:
            scrap_part = 'Actress'
        else:
            scrap_part = 'Film'
        
        if scrap_part != 'Actress':
            s_types = soup.select_one(".film-subtitle span").get_text(strip=True)
            s_type = s_types.split(" ‧ ")
    
            if s_type[1] == 'Drama':
                scrap_type = 'Drama'
            elif s_type[1] == 'Movie':
                scrap_type = 'Movie'
            elif s_type[1] == 'TV Program':
                scrap_type = 'TV Show'
                
            target = st.selectbox('Film Target', options=TITLE_OPTS, width='stretch')

    if "cast_results" not in st.session_state:
        st.session_state.cast_results = []
    if "film_results" not in st.session_state:
        st.session_state.film_results = []
    if "new_actress_results" not in st.session_state:
        st.session_state.new_actress_results = []
    if "drama_results" not in st.session_state:
        st.session_state.drama_results = []
    if "movie_results" not in st.session_state:
        st.session_state.movie_results = []
    if "tv_results" not in st.session_state:
        st.session_state.tv_results = []
    if "drama_index" not in st.session_state:
        st.session_state.drama_index = []
    if "movie_index" not in st.session_state:
        st.session_state.movie_index = []
    if "tv_index" not in st.session_state:
        st.session_state.tv_index = []
    if "scrap_exe" not in st.session_state:
        st.session_state.scrap_exe = False

    cast_df = st.session_state.cast_df.copy()
    actress_df = st.session_state.actress_df.copy()
        
    if st.button('Close', width='stretch'):
        st.session_state.scrap_dialog = False
        st.rerun()

    st.markdown('---')
    with st.container(horizontal=True):   
        show_scrap = st.button("Show", width='stretch')
        save_scrap = st.button("Save", width='stretch', type='primary')
    if st.button("Scrap", width='stretch', key='dialog-scrap'):
        st.session_state.scrap_exe = True
    st.markdown('---')

    if show_scrap:
        st.session_state.scrap_exe = False
        if scrap_part == "Cast":
            if st.session_state.cast_results:
                cast_scrap_df = pd.DataFrame(st.session_state.cast_results)
                st.write(cast_scrap_df)
            
            st.write(st.session_state.new_actress_results)
            if st.session_state.new_actress_results:
                new_actress_df = pd.DataFrame(st.session_state.new_actress_results)
                st.write(new_actress_df)
        elif scrap_part == 'Film':
            if st.session_state.film_results:
                film_scrap_df = pd.DataFrame(st.session_state.film_results)
                st.write(film_scrap_df)
        else:
            if not st.session_state.job_error:
                for drama in st.session_state.drama_index:
                    with st.container(horizontal=True):
                        with st.container(horizontal_alignment='center', width='content'):
                            st.image(drama['Picture'], width=110)
                        with st.container():
                            st.write(f'Title: {drama["Title"]}')
                            st.write(f'Episode: {drama["Episode"]}')
            else:
                st.warning('⚠️ Job Empty')
            
    if save_scrap:
        st.session_state.scrap_exe = False
        cast_results = st.session_state.cast_results.copy()
        if scrap_part == "Cast":
            cast_text = []
            cast_name_text = []
            actress_name_text = []
            actress_name_role_text = []
            selected_actress = []
            selected_actress_roles = []
            for i in range(len(cast_results)):
                cast_text.append(cast_results[i]["Name"])
                if cast_results[i]["Link"] in cast_df["Link"].values:
                    selected_cast_df = cast_df[cast_df["Link"] == cast_results[i]["Link"]]
                    if selected_cast_df["Link"].iloc[0] in st.session_state.actress_df['MDL'].values:
                        if selected_cast_df["Target Name"].iloc[0] != '--':
                            selected_actress.append(selected_cast_df["Target Name"].iloc[0])
                            selected_actress_roles.append(f'{selected_cast_df["Target Name"].iloc[0]}_ {cast_results[i]["Role"]}_ {cast_results[i]["Part"]}')
                        else:
                            selected_actress.append(cast_results[i]["Name"])
                            selected_actress_roles.append(f'{cast_results[i]["Name"]}_ {cast_results[i]["Role"]}_ {cast_results[i]["Part"]}')

                cast_name_text.append(f"{cast_results[i]['Link']}_ {cast_results[i]['Role']}_ {cast_results[i]['Part']}")

            if selected_actress and selected_actress_roles:
                actress_name_text = '_ '.join(selected_actress)
                if scrap_type == 'TV Show':
                    actress_name_role_text = 'Unqualified'
                else:
                    actress_name_role_text = ' ## '.join(selected_actress_roles)
            else:
                actress_name_text = 'No One'
                actress_name_role_text = 'Unqualified'
                            
            cast_text = "_ ".join(cast_text)
            cast_name_text = " ## ".join(cast_name_text)

            if target != "New":
                idx = df[df["Title"]==target].index[0]
                row = idx + 2
                df.at[idx, 'Cast'] = cast_text
                df.at[idx, 'Cast Name'] = cast_name_text
                df.at[idx, 'Actress Name'] = actress_name_text
                df.at[idx, 'Roles'] = actress_name_role_text

                st.session_state.film_df = df
                cells = [
                    {"range": f"K{row}", "values": [[actress_name_text]]},
                    {"range": f"O{row}", "values": [[actress_name_role_text]]},
                    {"range": f"R{row}", "values": [[cast_text]]},
                    {"range": f"S{row}", "values": [[cast_name_text]]},
                ]
                film_worksheet().batch_update(cells)
                st.toast('✅️ Cast and Cast Name added successfully!')
                time.sleep(.5)
                if st.session_state.new_actress_results:
                    new_actress_scrap_df = pd.DataFrame(st.session_state.new_actress_results)
                    new_actress_data = new_actress_scrap_df.values.tolist()

                    start_row = len(cast_df) + 2
                    end_row = start_row + len(new_actress_data) + 2
                    final_df = pd.concat([cast_df, new_actress_scrap_df], ignore_index=True)
                    st.session_state.cast_df = final_df
                    cast_worksheet().update(f"A{start_row}:D{end_row}", new_actress_data)
                    st.session_state.html_reset = True
            else:
                st.warning("No selected film")

        else:
            if target != "New":
                idx = df[df["Title"]==target].index[0]
                row = idx+2
                cells = [
                    {"range": f"C{row}", "values": [[st.session_state.film_results[0]['Picture']]]},
                    {"range": f"E{row}", "values": [[st.session_state.film_results[0]['Type']]]},
                    {"range": f"G{row}", "values": [[st.session_state.film_results[0]['Episode']]]},
                    {"range": f"N{row}", "values": [[st.session_state.film_results[0]['Synopsis']]]},
                    {"range": f"T{row}", "values": [[st.session_state.film_results[0]['Link']]]}
                ]

                film_worksheet().batch_update(cells)
                df.at[idx, 'Picture'] = st.session_state.film_results[0]['Picture']
                df.at[idx, 'Type'] = st.session_state.film_results[0]['Type']
                df.at[idx, 'Episode'] = st.session_state.film_results[0]['Episode']
                df.at[idx, 'Synopsis'] = st.session_state.film_results[0]['Synopsis']
                df.at[idx, 'Link'] = st.session_state.film_results[0]['Link']

                st.session_state.film_df = df
                st.toast('✅️ Scrap added successfully!')
                time.sleep(.5)
                st.session_state.html_reset = True
            else:
                if st.session_state.film_results[0]['Link']:
                    if st.session_state.film_results[0]['Type'] == 'Series':
                        playlist = st.session_state.film_results[0]['Country'] + ' Series'
                    elif st.session_state.film_results[0]['Type'] == 'Movie':
                        playlist = st.session_state.film_results[0]['Country'] + ' Movies'
                    else:
                        playlist = 'Variety Show'

                    new_row = [
                        'Not Watched',
                        'Want to Watch',
                        st.session_state.film_results[0]['Picture'],
                        st.session_state.film_results[0]['Title'],
                        st.session_state.film_results[0]['Type'],
                        '?',
                        st.session_state.film_results[0]['Episode'],
                        '--',
                        '?',
                        playlist,
                        'No One',
                        '--',
                        'Local',
                        st.session_state.film_results[0]['Synopsis'],
                        'Unqualified',
                        '--',
                        st.session_state.film_results[0]['Aired'],
                        '--',
                        '--',
                        st.session_state.film_results[0]['Link']
                    ]

                    film_worksheet().append_row(new_row)
                    df.loc[len(df)] = new_row
                    st.session_state.film_df = df
                    st.toast('✅️ Scrap added successfully!')
                    time.sleep(.5)
                    st.session_state.html_reset = True
                else:
                    st.warning('⚠️ Link is empty!')

    if file:
        if st.session_state.scrap_exe and scrap_part != 'Actress':
            cast_results = []
            new_actress_results = []
            film_results = []

            title = soup.select_one("h1.film-title").get_text(strip=True)


            st.subheader(title)

            if scrap_part != 'Cast':

                if target != 'New':
                    matched_film = df[df['Title'] == target].iloc[0]
                    pic = matched_film['Picture']
                    if 'placeholder' in pic:
                        pic = ''
                else:
                    title = st.text_input('Title:red[*]', width='stretch', value=title)
                    pic = ''

                poster = st.text_input('Poster:red[*]', width='stretch', value=pic, placeholder='Input your film poster URL...')

                if poster:
                    with st.container(horizontal_alignment='center'):
                        st.markdown("<h1 style='text-align: center;'>Poster</h1>", unsafe_allow_html=True)
                        st.image(poster, width=180)
                else:
                    poster = st.secrets.indicators.PLACEHOLDER_IMG_POSTER
            
            headers = soup.find_all("h3")
            if scrap_part == "Cast":
                if scrap_type == 'TV Show':
                    section_list = ["Main Host", "Regular Member", "Guest"]
                else:
                    section_list = ["Guest Role", "Support Role", "Main Role", "Cameo"]
                
                with st.container(horizontal=True):
                    for h3 in headers:
                        if h3.get_text(strip=True) in section_list:
                            ul = h3.find_next("ul")

                            for item in ul.find_all("li"):
                                name_tag = item.select_one("div.p-a-0 > a.text-primary")
                                name = name_tag.get_text(strip=True) if name_tag else "-"
                                profile_link = "https://mydramalist.com" + name_tag["href"]

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

                                with st.container():
                                    st.markdown('---')
                                    st.write(name)
                                    st.write(profile_link)
                                    st.image(img, width=80)
                                    st.write(character)
                                    st.write(role_part)

                                cast_results.append({
                                    "Name": name,
                                    "Link": profile_link,
                                    "Role": character,
                                    "Part": role_part
                                })

                                if profile_link not in cast_df['Link'].values.tolist():
                                    new_actress_results.append({
                                        "Name" : name,
                                        "Picture" : img.replace("s.jpg","c.jpg"),
                                        "Target Name" : "--",
                                        "Link" : profile_link
                                    })
                    
                    st.session_state.cast_results = cast_results
                    st.session_state.new_actress_results = new_actress_results
            else:
                st.markdown('---')
                film_link = soup.find("link", rel="canonical")
                film_ref = film_link.get("href") if film_link else '--'
                st.write(film_ref)
                
                synopsis_container = soup.find("div", class_="show-synopsis").find("p")
                synopsis = synopsis_container.get_text(" ", strip=True).replace("Edit Translation","")
                st.write(synopsis)
                
                for h3 in headers:
                    if h3.get_text(strip=True) == "Details":
                        next_div = h3.find_parent("div").find_next_sibling("div")
                        if next_div:
                            li_items = next_div.find_all("li")
                            for li in li_items:
                                label = li.find("b")
        
                                if label.get_text(strip=True) == 'Type:':
                                    film_type = li.find("span").get_text(strip=True)
                                    
                                    if not film_type:
                                        film_type = label.next_sibling.strip()

                                    if film_type == 'Drama':
                                        film_type = 'Series'
                                    elif film_type == 'TV Program':
                                        film_type = 'TV Show'
                                        
                                    st.write(film_type)
                                elif label.get_text(strip=True) == 'Country:':
                                    film_country = label.next_sibling.strip()
                                    st.write(film_country)
                                elif label.get_text(strip=True) == 'Episodes:':
                                    film_episode = label.next_sibling.strip()
                                    st.write(film_episode)
                                elif label.get_text(strip=True) in ['Aired:', 'Airs:', 'Release Date:']:
                                    film_release_date = label.next_sibling.strip()
                                    st.write(film_release_date)
                if scrap_type == 'Movie':
                    film_episode = '?'
                film_results.append({
                    "Title" : title,
                    "Synopsis" : synopsis,
                    "Type" : film_type,
                    "Country" : film_country,
                    "Episode" : film_episode,
                    "Aired" : film_release_date,
                    "Link" : film_ref,
                    "Picture" : poster
                })

                st.session_state.film_results = film_results
        elif st.session_state.scrap_exe and scrap_part == 'Actress':
            drama_results = []
            movie_results = []
            tv_results = []
            drama_index = []
            movie_index = []
            tv_index = []

            actress_name = soup.find("h1", class_='film-title').get_text(strip=True)
            filmography_section = soup.find_all("h5")
            for h5 in filmography_section:
                if h5.get_text(strip=True) == "Drama":
                    table = h5.find_next("table")
                    tbody = table.find("tbody")

                    for tr in tbody.find_all("tr"):
                        title = tr.find("td", class_="title")
                        img = title.find("img")["src"]
                        film_title = title.find("b").get_text(strip=True)
                        try:
                            film_link = title.find("a")["href"]
                            film_ref = "https://mydramalist.com" + film_link
                        except Exception as e:
                            film_ref = '--'

                        episode = tr.find("td", class_="episodes").get_text(strip=True)
                        
                        roles = tr.find("td", class_="role")
                        role = roles.find("div", class_="name").get_text(strip=True)
                        part = roles.find("div", class_="roleid").get_text(strip=True)

                        drama_results.append({
                            "Title": film_title,
                            "Episode": episode,
                            "Picture": img,
                            "Link": film_ref,
                            "Role Name": role,
                            "Role Part": part
                        })
                if h5.get_text(strip=True) == "Movie":
                    table = h5.find_next("table")
                    tbody = table.find("tbody")

                    for tr in tbody.find_all("tr"):
                        td = tr.find("td", class_="title")
                        img = td.find("img")["src"]
                        film_title = td.find("b").get_text(strip=True)
                        try:
                            film_link = td.find("a")["href"]
                            film_ref = "https://mydramalist.com" + film_link
                        except Exception as e:
                            film_ref = '--'

                        roles = tr.find("td", class_="role")
                        role = roles.find("div", class_="name").get_text(strip=True)
                        part = roles.find("div", class_="roleid").get_text(strip=True)

                        movie_results.append({
                            "Title": film_title,
                            "Picture": img,
                            "Link": film_ref,
                            "Role Name": role,
                            "Role Part": part
                        })

                if h5.get_text(strip=True) == "TV Show":
                    table = h5.find_next("table")
                    tbody = table.find("tbody")

                    for tr in tbody.find_all("tr"):
                        td = tr.find("td", class_="title")
                        img = td.find("img")["src"]
                        film_title = td.find("b").get_text(strip=True)
                        try:
                            film_link = td.find("a")["href"]
                            film_ref = "https://mydramalist.com" + film_link
                        except Exception as e:
                            film_ref = '--'

                        episode = tr.find("td", class_="episodes").get_text(strip=True)

                        roles = tr.find("td", class_="role")
                        role = roles.find("div", class_="name").get_text(strip=True)
                        part = roles.find("div", class_="roleid").get_text(strip=True)

                        tv_results.append({
                            "Title": film_title,
                            "Episode": episode,
                            "Picture": img,
                            "Link": film_ref,
                            "Role Name": role,
                            "Role Part": part
                        })
            
            if s_part in actress_df['MDL'].values:
                st.success(f'✅ {actress_name} was found in database!')
                match_actress = actress_df[actress_df['MDL'] == s_part]
                match_film = df[df['Actress Name'].str.contains(match_actress['Name (Stage)'].iloc[0], na=False)]
                match_cast = cast_df[cast_df['Link'] == s_part]

                st.write(match_actress) 
                st.write(match_film) 
                st.write(match_cast) 
            else:
                st.info(f'ℹ️ New Actress Detected')

            st.markdown('---')
            st.subheader('Film List')
            st.markdown('### Drama')
            for drama in drama_results:
                with st.container(horizontal=True):
                    if drama['Title'].lower() not in df['Title'].str.lower().values:
                        with st.container(width='content', vertical_alignment='center'):
                            if st.checkbox('', key=f'drama_{drama["Title"]}'):
                                check = True
                            else:
                                check = False

                        with st.container(horizontal_alignment='center', width='content'):
                            st.image(drama['Picture'], width=110)
                        with st.container():
                            st.write(f'Title: {drama["Title"]}')
                            st.write(f'Episode: {drama["Episode"]}')
                            if check:
                                playlist = st.selectbox('Playlist', key=f'new_playlist_{drama["Title"]}', options=PLAYLIST_OPTS)
                                if playlist != 'All':
                                    drama_index.append({
                                        'Status': 'Not Watched',
                                        'Info': 'Want to Watch',
                                        'Picture': 'https://res.cloudinary.com/devooeuej/image/upload/v1765969908/placeholder_poster.jpg',
                                        'Title': drama['Title'],
                                        'Type': 'Series',
                                        'Current Episode': '?',
                                        'Episode': drama['Episode'],
                                        'Genre': '--',
                                        'Rating': '?',
                                        'Playlist': playlist,
                                        'Actress Name': actress_name,
                                        'Note': '--',
                                        'Upload Type': 'Local',
                                        'Synopsis': '--',
                                        'Roles': f'{actress_name}_ --_ --',
                                        'Year': '--',
                                        'Aired': '--',
                                        'Cast': '--',
                                        'Cast Name': '--',
                                        'Link': drama['Link'],
                                    })
                    
            st.markdown('### Movie')
            for movie in movie_results:
                with st.container(horizontal=True):
                    if movie['Title'] not in df['Title'].values:
                        with st.container(width='content', vertical_alignment='center'):
                            if st.checkbox('', key=f'movie_{movie["Title"]}'):
                                check = True
                            else:
                                check = False

                        with st.container(horizontal_alignment='center', width='content'):
                            st.image(movie['Picture'], width=110)
                        with st.container():
                            st.write(f'Title: {movie["Title"]}')
                            if check:
                                playlist = st.selectbox('Playlist', key=f'new_playlist_{movie["Title"]}', options=PLAYLIST_OPTS)
                                if playlist != 'All':
                                    movie_index.append({
                                        'Status': 'Not Watched',
                                        'Info': 'Want to Watch',
                                        'Picture': 'https://res.cloudinary.com/devooeuej/image/upload/v1765969908/placeholder_poster.jpg',
                                        'Title': movie['Title'],
                                        'Type': 'Movie',
                                        'Current Episode': '?',
                                        'Episode': '?',
                                        'Genre': '--',
                                        'Rating': '?',
                                        'Playlist': playlist,
                                        'Actress Name': actress_name,
                                        'Note': '--',
                                        'Upload Type': 'Local',
                                        'Synopsis': '--',
                                        'Roles': f'{actress_name}_ --_ --',
                                        'Year': '--',
                                        'Aired': '--',
                                        'Cast': '--',
                                        'Cast Name': '--',
                                        'Link': movie['Link'],
                                    })

            st.markdown('### TV Show')
            for tv in tv_results:
                with st.container(horizontal=True):
                    if tv['Title'] not in df['Title'].values:
                        with st.container(width='content', vertical_alignment='center'):
                            if st.checkbox('', key=f'tv_{tv["Title"]}'):
                                check = True
                            else:
                                check = False

                        with st.container(horizontal_alignment='center', width='content'):
                            st.image(tv['Picture'], width=110)
                        with st.container():
                            st.write(f'Title: {tv["Title"]}')
                            st.write(f'Episode: {tv["Episode"]}')
                            if check:
                                playlist = st.selectbox('Playlist', key=f'new_playlist_{tv["Title"]}', options=PLAYLIST_OPTS)
                                if playlist != 'All':
                                    tv_index.append({
                                        'Status': 'Not Watched',
                                        'Info': 'Want to Watch',
                                        'Picture': 'https://res.cloudinary.com/devooeuej/image/upload/v1765969908/placeholder_poster.jpg',
                                        'Title': tv['Title'],
                                        'Type': 'Movie',
                                        'Current Episode': '?',
                                        'Episode': tv['Episode'],
                                        'Genre': '--',
                                        'Rating': '?',
                                        'Playlist': playlist,
                                        'Actress Name': actress_name,
                                        'Note': '--',
                                        'Upload Type': 'Local',
                                        'Synopsis': '--',
                                        'Roles': f'{actress_name}_ --_ --',
                                        'Year': '--',
                                        'Aired': '--',
                                        'Cast': '--',
                                        'Cast Name': '--',
                                        'Link': tv['Link'],
                                    })

            st.session_state.drama_index = drama_index
            st.session_state.movie_index = movie_index
            st.session_state.tv_index = tv_index
        else:
            if scrap_part != 'Actress':
                st.success('✅ HTML Detected! Ready to scrap!')
                st.info(f'ℹ️ Scrap Part Detected : {scrap_part}')
                st.info(f'ℹ️ Scrap Type Detected : {scrap_type}')
            elif scrap_part == 'Actress':
                st.info(f'ℹ️ Scrap Type Detected : Actress')
            else:
                st.error('❌ No Valid HTML Detected!')
    else:
        st.warning("No HTML detected!")

def complex_home():
    if 'log_out_btn' not in st.session_state:
        st.session_state.log_out_btn = False

    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Home Page</h1>", unsafe_allow_html=True)
    df_actress = init_dataframe_actress()
    df_film = init_dataframe_film()

    dummy_container = st.container()
    with dummy_container:
        st.write('')

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

def complex_film(device):
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
    if 'test' not in st.session_state:
        st.session_state.test = '--'
        

    if 'show_more_main' not in st.session_state:
        st.session_state.show_more_main = False
    if 'show_more_support' not in st.session_state:
        st.session_state.show_more_support = False
    if 'show_more_guest' not in st.session_state:
        st.session_state.show_more_guest = False
    if 'show_more_cameo' not in st.session_state:
        st.session_state.show_more_cameo = False
    if 'show_more_main_host' not in st.session_state:
        st.session_state.show_more_main_host = False
    if 'show_more_regular_member' not in st.session_state:
        st.session_state.show_more_regular_member = False
    if 'scrap_dialog' not in st.session_state:
        st.session_state.scrap_dialog = False
    

    if st.session_state.scroll_to_top:
        scroll_to_here(0,key='top')  # Scroll to the top of the page
        st.session_state.scroll_to_top = False
    if 'film_df' not in st.session_state:
        st.session_state.film_df = init_dataframe_film()
    
    df = st.session_state.film_df


    if 'actress_df' not in st.session_state:
        st.session_state.actress_df = init_dataframe_actress()

    actress_df = st.session_state.actress_df

    if 'cast_df' not in st.session_state:
        st.session_state.cast_df = init_dataframe_cast()

    cast_df = st.session_state.cast_df



    PLAYLIST_OPTS = ['All'] + sorted(
        df.loc[df['Playlist'] != 'All', 'Playlist']
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
        index = st.session_state.viewing_film_index

        if index is None or index >= len(df):
            st.warning("No film selected")
            st.stop()

        if st.session_state.editing_film_index == index:
            show_edit_film(index)
        else:
            show_view_film(index)

    def show_view_film(index):
        try:
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
                    st.text(text_synopsis, text_alignment='justify')
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
                            for actress_data in cast_list:
                                actress_role = actress_data.split('_ ')
                                actress_name = cast_df.loc[cast_df['Link'] == actress_role[0], 'Target Name']
                                if not actress_name.empty:
                                    if actress_name.iloc[0] == '--':
                                        actress_name = cast_df.loc[cast_df['Link'] == actress_role[0], 'Name'].iloc[0]
                                    else:
                                        actress_name = actress_name.iloc[0]

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
                            if st.button(f':orange-background[**{button_label}**]', width='content', type='tertiary', key=f"{actress_name}__{idx}", on_click=reset_page):
                                st.session_state.viewing_film_index = None
                                st.session_state.editing_film_index = None
                                st.session_state.search_text = actress_name
                                st.session_state.set_search = True
                                st.session_state.scroll_to_top = True
                                st.rerun()
                            if film['Cast Name'] != '--':
                                if actress_name in cast_role_df['Name'].values and actress_role_df.loc[actress_role_df['Name'] == actress_name, 'Role Part'].isin(['--']).any() and actress_role_df.loc[actress_role_df['Name'] == actress_name, 'Role Name'].isin(['--']).any():
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
                    status_icon = '🟡'
                    status_color = 'yellow'
                elif status_text == 'Dissapointing':
                    status_icon = '🟣'
                    status_color = 'violet'
                elif status_text == 'TBA':
                    status_icon = '🔵'
                    status_color = 'blue'
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
                if film['Rating'] == '?':
                    rate = 0
                else:
                    rate = film['Rating']
                st.markdown(f'## Ratings -- {rate}')
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
                    if film['Cast Name'] != '--':
                        other_casts = film['Cast Name'].split(' ## ')
                        other_cast_main = []
                        other_cast_support = []
                        other_cast_guest = []
                        other_cast_cameo = []
                        other_cast_regular_member = []
                        other_cast_main_host = []
                        count = 0
                        for cast in other_casts:
                            cast_data = cast.split('_ ')
                            cast_link = cast_data[0]
                            cast_role = cast_data[1]
                            cast_part = cast_data[2]
                            cast_data = cast_df[cast_df['Link'] == cast_link]
                            cast_name = cast_data['Name'].iloc[0]
                            if cast_data['Target Name'].iloc[0] != '--':
                                cast_target_name = cast_data['Target Name'].iloc[0]
                            else:
                                cast_target_name = cast_data['Name'].iloc[0]
                            if cast_target_name not in actress_list:
                                if cast_link in actress_df['MDL'].values:
                                    count+=1
                                
                                cast_img = cast_df[cast_df['Link'] == cast_link]
                                cast_pic = cast_img['Picture'].iloc[0]
                                if cast_part.lower() == 'main role':
                                    other_cast_main.append({
                                        'Picture' : cast_pic,
                                        'Name' : cast_name,
                                        'Role' : cast_role,
                                        'Part' : cast_part,
                                        'Link' : cast_link
                                    })
                                elif cast_part.lower() == 'support role':
                                    other_cast_support.append({
                                        'Picture' : cast_pic,
                                        'Name' : cast_name,
                                        'Role' : cast_role,
                                        'Part' : cast_part,
                                        'Link' : cast_link
                                    })
                                elif cast_part.lower() == 'guest role':
                                    other_cast_guest.append({
                                        'Picture' : cast_pic,
                                        'Name' : cast_name,
                                        'Role' : cast_role,
                                        'Part' : cast_part,
                                        'Link' : cast_link
                                    })
                                elif cast_part.lower() == 'cameo':
                                    other_cast_cameo.append({
                                        'Picture' : cast_pic,
                                        'Name' : cast_name,
                                        'Role' : cast_role,
                                        'Part' : cast_part,
                                        'Link' : cast_link
                                    })
                                elif cast_part.lower() == 'regular member':
                                    other_cast_regular_member.append({
                                        'Picture' : cast_pic,
                                        'Name' : cast_name,
                                        'Role' : cast_role,
                                        'Part' : cast_part,
                                        'Link' : cast_link
                                    })
                                elif cast_part.lower() == 'main host':
                                    other_cast_main_host.append({
                                        'Picture' : cast_pic,
                                        'Name' : cast_name,
                                        'Role' : cast_role,
                                        'Part' : cast_part,
                                        'Link' : cast_link
                                    })
                                elif cast_part.lower() == 'guest':
                                    other_cast_guest.append({
                                        'Picture' : cast_pic,
                                        'Name' : cast_name,
                                        'Role' : cast_role,
                                        'Part' : cast_part,
                                        'Link' : cast_link
                                    })
                        
                        if count > 0:
                            st.info(f'ℹ️ {count} Actress Found in database!')
                        if film['Type'] != 'TV Show':
                            st.markdown(f"<h2 style='text-align: center;'>Other Cast</h2>", unsafe_allow_html=True)
                            st.subheader(':orange-background[Main Role]')
                            if len(other_cast_main) > 0:
                                if not st.session_state.show_more_main:
                                    loop = min(3, len(other_cast_main))
                                else:
                                    loop = len(other_cast_main)

                                for i in range(loop):
                                    if other_cast_main[i]["Link"] in actress_df['MDL'].values:
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
                                    if other_cast_support[i]["Link"] in actress_df['MDL'].values:
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
                                    if other_cast_guest[i]["Link"] in actress_df['MDL'].values:
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
                                    if other_cast_cameo[i]["Link"] in actress_df['MDL'].values:
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
                            st.subheader(':orange-background[Main Host]')
                            if len(other_cast_main_host) > 0:
                                if not st.session_state.show_more_main_host:
                                    loop = min(3, len(other_cast_main_host))
                                else:
                                    loop = len(other_cast_main_host)

                                for i in range(loop):
                                    if other_cast_main_host[i]["Link"] in actress_df['MDL'].values:
                                        st.write(f':yellow-background[{i+1}. {other_cast_main_host[i]["Name"]}] ✅')
                                    else:
                                        st.write(f':yellow-background[{i+1}. {other_cast_main_host[i]["Name"]}]')
                                    with st.container(horizontal=True):
                                        st.image(other_cast_main_host[i]['Picture'], width=80)
                                        with st.container():
                                            st.write(f'Role Name : :gray-background[{other_cast_main_host[i]["Role"]}]')
                                            st.write(f'Role Part : :gray-background[{other_cast_main_host[i]["Part"]}]')
                                
                                if not st.session_state.show_more_main_host and len(other_cast_main_host) > min(3, len(other_cast_main_host)):
                                    if st.button('Show More 🔽', key='show_more_main_host'):
                                        st.session_state.show_more_main_host = True
                                        st.rerun()
                                elif st.session_state.show_more_main_host and len(other_cast_main_host) > min(3, len(other_cast_main_host)):
                                    if st.button('Show Less 🔼', key='show_less_main_host'):
                                        st.session_state.show_more_main_host = False
                                        st.rerun()
                            else:
                                st.write('--')

                            st.markdown('---')
                            st.subheader(':orange-background[Regular Member]')
                            if len(other_cast_regular_member) > 0:
                                if not st.session_state.show_more_regular_member:
                                    loop = min(3, len(other_cast_regular_member))
                                else:
                                    loop = len(other_cast_regular_member)

                                for i in range(loop):
                                    if other_cast_regular_member[i]["Link"] in actress_df['MDL'].values:
                                        st.write(f':yellow-background[{i+1}. {other_cast_regular_member[i]["Name"]}] ✅')
                                    else:
                                        st.write(f':yellow-background[{i+1}. {other_cast_regular_member[i]["Name"]}]')
                                    with st.container(horizontal=True):
                                        st.image(other_cast_regular_member[i]['Picture'], width=80)
                                        with st.container():
                                            st.write(f'Role Name : :gray-background[{other_cast_regular_member[i]["Role"]}]')
                                            st.write(f'Role Part : :gray-background[{other_cast_regular_member[i]["Part"]}]')
                                
                                if not st.session_state.show_more_regular_member and len(other_cast_regular_member) > min(3, len(other_cast_regular_member)):
                                    if st.button('Show More 🔽', key='show_more_regular_member'):
                                        st.session_state.show_more_regular_member = True
                                        st.rerun()
                                elif st.session_state.show_more_regular_member and len(other_cast_regular_member) > min(3, len(other_cast_regular_member)):
                                    if st.button('Show Less 🔼', key='show_less_regular_member'):
                                        st.session_state.show_more_regular_member = False
                                        st.rerun()
                            else:
                                st.write('--')

                            st.markdown('---')
                            st.subheader(':orange-background[Guest]')
                            if len(other_cast_guest) > 0:
                                if not st.session_state.show_more_guest:
                                    loop = min(3, len(other_cast_guest))
                                else:
                                    loop = len(other_cast_guest)

                                for i in range(loop):
                                    if other_cast_guest[i]["Link"] in actress_df['MDL'].values:
                                        st.write(f':yellow-background[{i+1}. {other_cast_guest[i]["Name"]}] ✅')
                                    else:
                                        st.write(f':yellow-background[{i+1}. {other_cast_guest[i]["Name"]}]')
                                    with st.container(horizontal=True):
                                        st.image(other_cast_guest[i]['Picture'], width=80)
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
                    else:
                        st.warning('No Info') 
                    st.markdown('---')
                except Exception as e:
                    st.write('ℹ️ Error : Update it from Data Bank ℹ️', e)
            with tab_cast_setting:
                if film['Cast Name'] != '--':

                    if film['Type'] != 'TV Show':
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
                    else:
                        act_part = st.radio('Role Part', options=['Main Host', 'Regular Member', 'Guest'], horizontal=True)
                        if act_part == 'Main Host':
                            max_val = len(other_cast_main_host)
                            role_part_df = pd.DataFrame(other_cast_main_host)
                        elif act_part == 'Regular Member':
                            max_val = len(other_cast_regular_member)
                            role_part_df = pd.DataFrame(other_cast_regular_member)
                        elif act_part == 'Guest':
                            max_val = len(other_cast_guest)
                            role_part_df = pd.DataFrame(other_cast_guest)
                    
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
                                cast_df.at[idx, 'Target Name'] = target_name
                                st.session_state.cast_df = cast_df
                                cast_worksheet().update(f'C{row}', target_name)
                                st.toast('✅ **:yellow[Target Name]** Added Successfully!')
                                time.sleep(.5)
                                st.rerun()
                            else:
                                save_error = '⚠️ Target Name Cannot be "No One"'
                        if st.button('Add Cast', width='stretch'):
                            if target_name != 'No One':
                                row = idx+2
                                cast_df.at[idx, 'Target Name'] = target_name
                                st.session_state.cast_df = cast_df
                                cast_worksheet().update(f'C{row}', target_name)

                                row = index+2
                                if df['Actress Name'].loc[index] == 'No One':
                                    df.at[index, 'Actress Name'] = target_name
                                    df.at[index, 'Roles'] = f'{target_name}_ {act_info["Role"]}_ {act_info["Part"]}'
                                else:
                                    df.at[index, 'Actress Name'] += f'_ {target_name}'
                                    df.at[index, 'Roles'] += f' ## {target_name}_ {act_info["Role"]}_ {act_info["Part"]}'
                                
                                if df['Type'].iloc[index] == 'TV Show':
                                    df.at[index, 'Roles'] = 'Unqualified'

                                new_data = df.iloc[index].values.tolist()
                                st.session_state.film_df = df
                                film_worksheet().update(f'A{row}:T{row}', [new_data])

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
        except Exception as e:
            st.write(e)
            if st.button('⚠️ Emergency Close ⚠️', width='stretch'):
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

        st.session_state.status = '--'

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

            edited_title = st.text_area('Title:red[*]', placeholder='Enter film title...', value=film['Title'], key=f'film_title_{index}')

            if pd.notna(film['Synopsis']) and film['Synopsis'] != '⚠️ Synopsis not found!':
                text_synopsis = film['Synopsis']
            else:
                text_synopsis = ''

            edited_synopsis = st.text_area('Synopsis', placeholder='Enter film synopsis...', value=text_synopsis, key=f'film_synopsis_{index}')
            
            if edited_synopsis == '':
                edited_synopsis = '⚠️ Synopsis not found!'
            
            if film['Cast Name'] != '--':
                if film['Actress Name'] != 'No One':
                    actress_list = []
                    name_map = cast_df.set_index('Link')[['Name', 'Target Name']].to_dict('index')
                    for i in film['Cast Name'].split(' ## '):
                        roles = i.strip()
                        role = roles.split('_ ')
                        
                        link = role[0]

                        if link in name_map:
                            if link in st.session_state.actress_df['MDL'].values:
                                target = name_map[link]['Target Name']
                                act_name = target if target != '--' else name_map[link]['Name']

                                if act_name in ACTRESS_OPTS:
                                    actress_list.append(act_name)
                else:
                    actress_list = ['No One']
            else:
                actress_list = [
                    j.strip() for j in film['Actress Name'].split('_ ')
                    if j.strip() in ACTRESS_OPTS
                ]

            selected_actress = st.multiselect(
                'Actress:red[*]', 
                options = ACTRESS_OPTS, 
                default = actress_list
            )

            edited_actress = "_ ".join(selected_actress)

            if film['Genre'] == '[PLACEHOLDER]':
                genre_text = []
            else:
                genre_text = [
                    j.strip() for j in film['Genre'].split(',')
                    if j.strip() in GENRE_OPTS
                ]

            selected_genre = st.multiselect(
                'Genre:red[*]', 
                options = GENRE_OPTS, 
                default = genre_text
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
                if st.session_state.status != 'TBA':
                    edited_eps = st.number_input('Episode',min_value=1, value=eps)
                else:
                    edited_eps = '?'
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
                if film['Current Episode'] == '?':
                    current_eps = 1
                else:
                    current_eps = int(film['Current Episode'])

                edited_current_eps = st.number_input('Current Episode', min_value=1, max_value=int(film['Episode']), value=current_eps)
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
                status_index = 1
            elif film['Status'] == 'TBA':
                status_index = 2
            else:
                status_index = 0
            
            st.radio('Status', options=['--', 'Recommended', 'TBA'], index=status_index, horizontal=True, key='status')

            if st.session_state.status == 'Recommended':
                edited_status = 'Recommended'
            elif st.session_state.status == 'TBA':
                edited_status = 'TBA'
                if not selected_genre:
                    edited_genre = '[PLACEHOLDER]'
                    
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
                    else:
                        actress_role_df = pd.DataFrame(columns=['Name', 'Role Name', 'Role Part'])

                    for idx in selected_actress_data.index:
                        data = selected_actress_data.loc[idx]

                        if not actress_role_df.empty:
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
                                role_part_text = role_data['Role Part'].replace(' Role','')
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
            if selected_actress and edited_title and edited_genre and not errors:
                with st.container(horizontal=True):
                    if st.button("💾 Save", width='stretch', type="primary", key=f"save_{index}"):
                        join_code = edited_title
                        clean_code = re.sub(r'[^\w]', '', join_code)
                        clean_code = "N" + clean_code

                        old_filename = str(film['Picture']).split('/')[-1]
                        old_public_id = old_filename.split('.')[0]

                        # kalau cuma ganti foto
                        if (new_pic and new_pic != '') and (edited_title == film['Title']) and new_pic != film['Picture']:
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
                            
                            st.toast('ℹ️ Photo Changed')

                        # kalau ganti foto dan code
                        elif (new_pic and new_pic != '') and (film['Title'] != edited_title):
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
                            st.toast('ℹ️ Photo and Title Changed')
                        
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
                            st.toast('ℹ️ Title Changed')
                        else:
                            final_picture_url = film['Picture']
                            st.toast('ℹ️ Nothing Changed')

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
            else:
                st.warning('⚠️ Fill Mandatory Fields First! (:red[*])')
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

            with st.container(horizontal=True):
                if st.toggle('Recommended'):
                    new_status = 'Recommended'
            
                if st.toggle('TBA'):
                    new_status = 'TBA'
                    if not selected_genre:
                        new_genre = '[PLACEHOLDER]'
            
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
            else:
                st.warning('⚠️ Fill Mandatory Fields First! (:red[*])')
                errors = True

        if st.button('Close', type='primary', width='stretch'):
            st.rerun()
    
    st.markdown(
        """
        <style>
        .st-key-film-navbar {
            background-color: #1D546D;
            padding: 5px;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    film_navbar = st.container(key='film-navbar', width='stretch', horizontal=True, horizontal_alignment='distribute')

    with film_navbar:
        if st.button('🏠 Home', width='content', on_click=reset_page):
            return 'home'
        
        with st.container(horizontal_alignment='right', horizontal=True):
            if st.button('➕ Actress', width='content'):
                @st.dialog('Add New Actress',width='small')
                def show_dialog_add():
                    new_act_error = False
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
                    
                    st.markdown('---')
                    if st.button('Add Actress', width='stretch', type='primary'):
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
                    if st.button('❌ Close', width='stretch'):
                        st.rerun()
                show_dialog_add()
            
        if st.button('💻 Scrap', width='content'):
            st.session_state.scrap_dialog = True
    
    film_navbar.float("top: 50px;z-index: 999990;")

    # Main
    st.space('small')
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Film List</h1>", unsafe_allow_html=True)
    filtered_df = df.copy()

    with st.sidebar:
        st.write('📌 Filter')
        show_recommend = st.toggle('Recommended', on_change=reset_page, key='show_recommend')
        show_tba = st.toggle('TBA', on_change=reset_page, key='show_tba')
        show_poster = st.toggle('Placeholder Poster', on_change=reset_page, key='show_poster')
        st.markdown('---')
        st.write('⚙️ Page Option')
    
    
    if st.session_state.viewing_film_index is not None or st.session_state.viewing_bank_index != []:
        show_film_details()
    
    if st.session_state.scrap_dialog:
        display_scrap_manual()


    if show_recommend:
        filtered_df = filtered_df[filtered_df['Status'] == 'Recommended']
    if show_tba:
        filtered_df = filtered_df[filtered_df['Status'] == 'TBA']
    if show_poster:
        filtered_df = filtered_df.loc[filtered_df['Picture'].str.contains('placeholder', na=False)]
    
    filtered_df = filtered_df.sort_values(by='Title', ascending=True)
    
    display_film_grid(filtered_df, actress_df, device)
        
    st.markdown('---')
    if st.button('⬆️ Back to top', width='stretch'):
        st.session_state.scroll_to_top = True
        st.rerun()
    with st.sidebar:
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

def complex_actress(device):

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
    def refresh_data():
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
        actress_list = film['Actress Name'].split('_ ')
        if film['Type'] != 'TV Show':
            role_list = film['Roles'].split(' ## ')
            role_dict = []
            for roles in role_list:
                role = roles.split('_ ')
                role_dict.append({
                    'Name': role[0],
                    'Role': role[1],
                    'Part': role[2]
                })
            role_df = pd.DataFrame(role_dict)

        matching_actresses = filtered_actress_df[filtered_actress_df['Name (Stage)'].isin(actress_list)]

        for i in range(0,len(matching_actresses)):
            if film['Type'] != 'TV Show':
                info = role_df[role_df['Name'] == matching_actresses['Name (Stage)'].iloc[i]].iloc[0]
                act_name = info['Name']
                act_role = info['Role']
                act_part = info['Part']
            
            with st.container(horizontal=True):
                st.image(matching_actresses['Picture'].iloc[i], width=80)
                with st.container():
                    if film['Type'] != 'TV Show':
                        st.markdown(f"### {act_name}")
                        st.write(f"{act_role} - {act_part}")
                    else:
                        st.markdown(f'### {matching_actresses["Name (Stage)"].iloc[i]}')
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
        
        st.markdown('---')
        st.markdown('## Rating')
        with st.container(key='star_rating'):
            if film['Rating'] == '?':
                st.write('🌑🌑🌑🌑🌑')
            else:
                if film['Rating']%1 == 0:
                    st.write('🌕' * int(film["Rating"]) + '🌑' * (5-int(film['Rating'])))
                else:
                    st.write('🌕' * int(film["Rating"]) + '🌗' + '🌑' * (5-(int(film['Rating'])+1)))
        
        st.markdown('---')
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
            refresh_data()
        
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
        filtered_df = filtered_df.sort_values(by='Name (Stage)', ascending=True)

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
                        if actress['Favourite'] == True:
                            border_color = '947B27'
                        else:
                            border_color = '374151'

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
                                border: 2px solid #{border_color};
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
