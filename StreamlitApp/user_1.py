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
    "Thailand"
]

# MOVIE OPTS
STATUS_OPTS = [
    "Not Watched",
    "Watched",
    "Goat",
    "Dissapointing"
]

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
    "Sci-Fi"
]

TYPE_OPTS = [
    "Movie",
    "Series"
]


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


def load_data_actress(conn):
    try:
        df = conn.read(worksheet="NList", usecols=list(range(10)))
        df = values_handling(df,'actress')
        # df = initial_load(df,'actress')
        return df
    except Exception as e:
        return pd.DataFrame()

def load_data_film(conn):
    try:
        df = conn.read(worksheet="NFilm", usecols=list(range(12)))
        return df
    except Exception as e:
        return pd.DataFrame()
    
def update_google_sheets(df,conn,type):
    try:
        st.toast("✅ Google Sheets updated successfully!")
        if not isinstance(df, pd.DataFrame):
            st.error("Data must be a pandas DataFrame")
            return False
        
        df_to_update = df.copy()
        if type == 'actress':
            sheet = 'NList'
        else:
            sheet = 'NFilm'
            
        conn.update(
            worksheet=sheet, 
            data=df_to_update
        )
        return True
    except:
        return False

def init_dataframe_actress(conn):
    """Inisialisasi DataFrame di session state"""
    if "actress_df" not in st.session_state:
        df = load_data_actress(conn)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Review', 'Picture', 'Name (Alphabet)', 'Name (Native)',
                'Birthdate', 'Age', 'Nationality', 'Height (cm)', 'Job',
                'Favourite'
            ])
        
        st.session_state.actress_df = df
        st.session_state.data_loaded = True
        return df
    else:
        return st.session_state.actress_df

def init_dataframe_film(conn):
    """Inisialisasi DataFrame di session state"""
    if "film_df" not in st.session_state:
        df = load_data_film(conn)
        if df.empty:
            df = pd.DataFrame(columns=[
                'Status', 'Info', 'Picture', 'Title', 'Current Episode',
                'Episode', 'Genre', 'Rating', 'Playlist'
            ])
        
        st.session_state.film_df = df
        st.session_state.data_loaded = True
        return df
    else:
        return st.session_state.film_df    
def reset_page():
    """Reset halaman ke 1"""
    st.session_state.film_page = 1

# --- FUNGSI ALTERNATIF: Grid Layout tanpa Pagination ---
def display_film_grid(df, actress_df):
    """
    Menampilkan semua card sekaligus dalam grid
    """
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
    with st.container(horizontal=True, vertical_alignment='bottom'):
        search_name = st.text_input("🔍 Search (Title):", placeholder="Enter Movie or Series...", key='search_bar', on_change=reset_page)
        if st.button('Clear', on_click=reset_page):
            st.session_state.search_reset = True
            st.rerun()
    playlist_filter = st.selectbox("Playlist:", options=PLAYLIST_OPTS, on_change=reset_page)
    info_filter = st.selectbox("Info:", options=INFO_OPTS_MIX, on_change=reset_page)

    if search_name:
        mask = filtered_df['Title'].str.contains(search_name, case=False, na=False)
        filtered_df = filtered_df[mask]
        # st.session_state.film_page = 1

    if playlist_filter != 'All':
        filtered_df = filtered_df[filtered_df['Playlist'] == playlist_filter]  
        # st.session_state.film_page = 1

    if info_filter != 'All':
        filtered_df = filtered_df[filtered_df['Info'] == info_filter]
        # st.session_state.film_page = 1

    total_pages = max(1, (len(filtered_df) + 15 - 1) // 15)  

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
                
                if st.button('➡️',key='next_top', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,)):
                    st.session_state.scroll_to_here = True
                
        
        page = st.session_state.film_page
        
        start_idx = (page - 1) * 15 
        end_idx = min(start_idx + 15, len(filtered_df)) 
        st.markdown("---")
        st.caption(f"Showing {start_idx+1}-{end_idx} from {len(filtered_df)} actress")
        
        rows_to_display = filtered_df.iloc[start_idx:end_idx] 
        for i in range(0, len(rows_to_display)): # len = 8 // i = [0,8]
            if i < len(rows_to_display):
                film = rows_to_display.iloc[i]
                real_index = rows_to_display.index[i]
            
                st.image(
                    film['Picture'],
                    caption=film['Title'],
                    width='stretch'
                )

                with st.expander('📋 View Details', expanded=False):
                    st.markdown(f"**🎬 {film['Type']}**")
                    
                    if film['Type'] == 'Series':
                        st.markdown (f"🕑 {film['Current Episode']}/{film['Episode']}")
                    st.markdown (f"📁 {film['Genre']}")
                    if film['Rating'] == '?' or film['Rating'] == 0:
                        st.markdown ("🤩 --")
                    else:
                        st.markdown (f"🤩 {'⭐' * int(film['Rating'])}")
                    
                    info_text = film['Info']
                    status_text = film['Status']

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
                    elif status_text == 'Goat':
                        status_icon = '🟣'
                        status_color = 'violet'
                    else:
                        status_icon = '⚪'
                        status_color = 'grey'

                    st.markdown (f"👩‍🦰 Actress")
                    actress_list = film['Actress Name'].split(', ')
                    matching_actresses = filtered_actress_df[filtered_actress_df['Name (Alphabet)'].isin(actress_list)]
                    if len(matching_actresses)>2:
                        is_center = 'center'
                    else:
                        is_center = 'left'
                    with st.container(horizontal=True, horizontal_alignment=is_center):
                        for index in matching_actresses.index:
                            st.image(
                                matching_actresses['Picture'][index],
                                width=80,
                                caption=matching_actresses['Name (Alphabet)'][index]
                            )
                    st.markdown(f'ℹ️ Information')
                    with st.container(horizontal=True):
                        st.badge(f"{status_text}",icon=status_icon, color=status_color)
                        st.badge(f"{info_text}",icon=info_icon, color=info_color)
                    
                    st.markdown(f'📋 Notes')
                    st.warning(film['Note'])
                    with st.container(horizontal=True):
                        if st.button('✏️ Edit', key=f'film_edit_{real_index}', width='stretch'):
                            st.session_state.viewing_film_index = real_index
                            st.session_state.editing_film_index = real_index
                            st.rerun()
                    
                st.space('small') 
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
        else:
            with st.container(key='page_button_bottom', horizontal=True, horizontal_alignment='center'):
                if st.button('⬅️',key='previous_bottom', disabled=(st.session_state.film_page == 1), on_click=set_page, args=(st.session_state.film_page-1,)):
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
                        key=f'page_bottom_{i}',
                        disabled=(i == st.session_state.film_page),
                        on_click=set_page,
                        args=(i,)
                    ):
                        st.session_state.scroll_to_here = True
                
                if st.button('➡️',key='next_bottom', disabled=(st.session_state.film_page == total_pages), on_click=set_page, args=(st.session_state.film_page+1,)):
                    st.session_state.scroll_to_here = True                 
    else:
        st.info('No film match the filter')


def complex_home(conn):
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Home Page</h1>", unsafe_allow_html=True)
    df_actress = init_dataframe_actress(conn)
    df_film = init_dataframe_film(conn)

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
                    st.metric('Goat', len(df_film[df_film['Status'] == 'Goat']))
            if st.button('Go To Film →'):
                return 'film'
    
    if st.button('🔐 Logout', width='stretch', type='primary'):
        st.session_state.clear()
        return 'login'
    
    # CSS custom untuk container tertentu
    st.markdown("""
    <style>
    /* Container dengan key ActressList */
    .st-key-ActressList {
        background-color: #ffc629; /* Pink soft */
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
        background-color: #40b3ff; /* Pink soft */
        padding: 30px 20px 50px 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


def complex_film(conn):
    # Inisialisasi variabel kontrol
    if "editing_film_index" not in st.session_state:
        st.session_state.editing_film_index = None
    if "viewing_film_index" not in st.session_state:
        st.session_state.viewing_film_index = None
    if 'scroll_to_top' not in st.session_state:
        st.session_state.scroll_to_top = False
    if 'scroll_to_here' not in st.session_state:
        st.session_state.scroll_to_here = False

    if st.session_state.scroll_to_top:
        scroll_to_here(0,key='top')  # Scroll to the top of the page
        st.session_state.scroll_to_top = False

    df = init_dataframe_film(conn)
    actress_df = init_dataframe_actress(conn)

    PLAYLIST_OPTS = ['All'] + sorted(
        df.loc[df['Playlist'] != 'All', 'Playlist']
        .dropna()
        .unique()
        .tolist()
    )

    ACTRESS_OPTS = ['No One'] + sorted(
        actress_df.loc[actress_df['Name (Alphabet)'] != 'No One', 'Name (Alphabet)']
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
        film = df.iloc[index]

        with st.container(key='poster_code', horizontal_alignment='center'):
            st.markdown(f"<h2 style='text-align: center;'>{film['Title']}</h2>", unsafe_allow_html=True)
            st.image(film['Picture'], width=200)
        
        st.markdown('### Actress')
        st.write(film['Actress Name'])
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

        with st.container(key='view_film_edit_container_button', horizontal=True):
            if st.button('✏️ Edit', width='stretch'):
                st.session_state.editing_film_index = index
                st.rerun()
            if st.button('❌ Close', width='stretch'):
                st.session_state.viewing_film_index = None
                st.session_state.editing_film_index = None
                st.rerun()
            if st.button("🗑️ Delete Actress", width='stretch', type="secondary", key=f"delete_{index}"):
                delete_film(index)

    def show_edit_film(index):
        film = df.iloc[index]

        playlist_index = PLAYLIST_OPTS.index(film['Playlist']) if film['Playlist'] in PLAYLIST_OPTS else 0
        info_s_index = INFO_OPTS_S.index(film['Info']) if film['Info'] in INFO_OPTS_S else 0
        info_m_index = INFO_OPTS_M.index(film['Info']) if film['Info'] in INFO_OPTS_M else 0
        status_index = STATUS_OPTS.index(film['Status']) if film['Status'] in STATUS_OPTS else 0
        type_index = TYPE_OPTS.index(film['Type']) if film['Type'] in TYPE_OPTS else 0


        with st.container(horizontal_alignment='center'): 
            st.markdown(f"### ✏️ Editing: {film['Title']}")
            st.image(film['Picture'], width=250)
            new_pic = st.file_uploader('Change Image', type=['png', 'jpg', 'jpeg', 'webp'], key=f'film_picture_{index}')
            if new_pic is not None:
                st.image(new_pic, width=250)
    
        
        st.subheader("Basic Information")
        # edited_name = st.text_input('Actress', placeholder='Enter actress name... (e.g. Miyashita Rena)', value=film['Actress Name'], key=f'film_name_{index}')
        edited_status = st.selectbox('Status', options=STATUS_OPTS, index=status_index)

        edited_title = st.text_area('Title', placeholder='Enter film title...', value=film['Title'], key=f'film_title_{index}')
        
        selected_actress = st.multiselect(
            'Actress', 
            options = ACTRESS_OPTS, 
            default = [
                j.strip() for j in film['Actress Name'].split(',')
                if j.strip() in ACTRESS_OPTS
            ]
        )

        edited_actress = ", ".join(selected_actress)

        # if st.checkbox('New Actress', key='new_actress_check'):
        #     edited_actress = '?'
        #     edited_actress_input = st.text_input('New Actress Name*', placeholder='Alphabet, Kanji')
        #     if edited_actress_input:
        #         try:
        #             edited_actress_name, edited_actress_native = edited_actress_input.split(', ')
        #             st.write('Name: ', edited_actress_name)
        #             st.write('Kanji: ', edited_actress_native)
        #         except Exception as e:
        #             st.error(f'Error new actress: {e}')
            
        #     edited_nationality = st.selectbox('New Actress Nationality', options=COUNTRY_OPTS)
        # elif selected_actress:
        #     edited_actress = ", ".join(selected_actress)
        #     edited_actress_input = '?'
        # else:
        #     edited_actress = '?'
        #     edited_actress_input = '?'

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

        if edited_type == 'Series':
            if film['Episode'] == '?':
                eps = 1
            else:
                eps = int(film['Episode'])
            edited_eps = st.number_input('Episode',min_value=1, value=eps)
            edited_info = st.selectbox('Info', options=INFO_OPTS_S, index=info_s_index)
        else:
            edited_eps = '?'
            edited_info = st.selectbox('Info', options=INFO_OPTS_M, index=info_m_index)

        if edited_info == 'On Going':
            if film['Current Episode'] == '?':
                current_eps = 1
            else:
                current_eps = int(film['Current Episode'])

            edited_current_eps = st.number_input('Current Episode', min_value=1, max_value=int(film['Episode']), value=current_eps)
            edited_rating = '?'
        elif edited_info == 'Complete':
            edited_current_eps = edited_eps
            if film['Rating'] == '?':
                edited_rating = st_star_rating('Rating', maxValue=5, defaultValue=3, key="rating", emoticons=True)
            else:
                edited_rating = st_star_rating('Rating', maxValue=5, defaultValue=int(film['Rating']), key="rating", emoticons=True)
        elif edited_info == 'Dissapointing':
            edited_current_eps = '?'
            edited_rating = 0
        else:
            edited_current_eps = '?'
            edited_rating = '?'
            
        edited_playlist = st.selectbox('Playlist', options=PLAYLIST_OPTS, index=playlist_index, key=f'film_playlist_{index}')
        
        if st.checkbox('New Playlist'):
            new_playlist = st.text_input('New Playlist', placeholder='Enter new playlist...', key=f'film_new_playlist_{index}')
            if new_playlist != '' or new_playlist != None:
                edited_playlist = new_playlist
        
        if film['Note'] == '--':
            notes = ''
        else:
            notes = film['Note']
        edited_note = st.text_area('Note', placeholder='How do you think about the film/series...', value=notes)

        if edited_note == '':
            edited_note = '--'
        
        # Tombol aksi

        with st.container(horizontal=True):
            if st.button("💾 Save", width='stretch', type="primary", key=f"save_{index}"):
                join_code = edited_title
                clean_code = re.sub(r'[^\w]', '', join_code)
                clean_code = "N" + clean_code

                old_filename = str(film['Picture']).split('/')[-1]
                old_public_id = old_filename.split('.')[0]

                # if ((edited_actress!='?')or(edited_actress_input!='?')):
                #     if edited_actress_input!='?':
                #         # Create edited row data
                #         edited_row = pd.DataFrame([{
                #             'Review': 'Not Checked',
                #             'Picture': st.secrets.indicators.PLACEHOLDER_IMG,
                #             'Name (Alphabet)': edited_actress_name,
                #             'Name (Native)': edited_actress_native,
                #             'Birthdate': '?',
                #             'Age': '?',
                #             'Nationality': edited_nationality,
                #             'Height (cm)': '? cm',
                #             'Job': 'Actress',
                #             'Favourite': '0',

                #         }])
                    
                #         # Add to DataFrame
                #         edited_name_native = edited_row['Name (Native)'].iloc[0]
                #         df_actress = st.session_state.actress_df

                #         if edited_name_native in df_actress['Name (Native)'].values:
                #             st.warning(f"⚠️ Actress '{edited_name_native}' already exist in database with name!")
                #             st.stop()
                #         else:
                #             df_actress = pd.concat([df_actress, edited_row], ignore_index=True)   
                #             df_actress = df_actress.sort_values('Name (Alphabet)', key=lambda col: col.str.lower(), ascending=True, ignore_index=True)
                #             # Update ke Google Sheets
                #             if update_google_sheets(df_actress,conn,'actress'):
                #                 st.success("✅ edited actress added successfully to Google Sheets!")
                #                 st.session_state.actress_df = values_handling(df_actress,'actress')  # Update session state
                #             else:
                #                 st.error("❌ Failed to add edited actress to Google Sheets")
                #                 st.stop()
                #         edited_actress = edited_actress_name

                # kalau cuma ganti foto
                if new_pic and (edited_title == film['Title']):
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                        try:
                            delete_cloudinary_image(old_public_id)
                        except Exception as e:
                            st.warning(f"Could not delete old image: {e}")
                            st.stop()
                    final_picture_url = upload_to_database(new_pic, clean_code)
                    if not final_picture_url:
                        st.error("Failed to upload new image")
                        st.stop()
                # kalau ganti foto dan code
                elif new_pic and (film['Title'] != edited_title):
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                        try:
                            delete_cloudinary_image(old_public_id)
                        except Exception as e:
                            st.warning(f"Could not delete old image: {e}")
                            st.stop()
                        final_picture_url = upload_to_database(new_pic, clean_code)
                        if not final_picture_url:
                            st.error("Failed to upload new image")
                            st.stop()
                # kalau cuma ganti code
                elif not new_pic and (film['Title'] != edited_title):
                    if pd.notna(film['Picture']) and film['Picture'] and "placeholder" not in str(film['Picture']).lower():
                        try:
                            final_picture_url = rename_cloudinary_image(old_public_id, clean_code)
                        except Exception as e:
                            st.warning(f'Could not rename old image: {e}')
                            st.stop()
                else:
                    final_picture_url = film['Picture']
                    
                # Update data di DataFrame
                df.at[index, 'Status'] = edited_status
                df.at[index, 'Info'] = edited_info
                df.at[index, 'Picture'] = final_picture_url
                df.at[index, 'Actress Name'] = edited_actress
                df.at[index, 'Title'] = edited_title
                df.at[index, 'Type'] = edited_type
                df.at[index, 'Current Episode'] = edited_current_eps
                df.at[index, 'Episode'] = edited_eps
                df.at[index, 'Genre'] = edited_genre
                df.at[index, 'Rating'] = edited_rating
                df.at[index, 'Playlist'] = edited_playlist
                df.at[index, 'Note'] = edited_note
                
                # Update ke Google Sheets
                if update_google_sheets(df,conn,'film'):
                    st.session_state.film_df = values_handling(df,'film')  # Update session state
                else:
                    st.error("❌ Failed to update Google Sheets")
                    st.stop()
                
                st.session_state.editing_film_index = None
                st.session_state.viewing_film_index = None
                st.rerun()
                
            if st.button('❌ Close', width='stretch'):
                st.session_state.viewing_film_index = None
                st.session_state.editing_film_index = None
                st.rerun()

        if st.button("🗑️ Delete Film", width='stretch', type="secondary", key=f"delete_{index}"):
            delete_film(index)
    
    def delete_film(index):
        film = df.loc[index]
        pic_filename = str(film['Picture']).split('/')[-1]
        pic_id = pic_filename.split('.')[0]

        if 'placeholder' not in pic_id:
            delete_cloudinary_image(pic_id)

        df.drop(index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Update ke Google Sheets
        if update_google_sheets(df,conn,'film'):
            st.session_state.film_df = values_handling(df,'film') 
        else:
            st.error("❌ Failed to delete actress from Google Sheets")
            st.stop()
        
        st.session_state.editing_film_index = None
        st.session_state.viewing_film_index = None
        st.rerun()

    @st.dialog("➕ Add New Film", width='small')
    def add_new_film():
        if st.session_state.get('film_reset', False):
            st.session_state.film_reset = False
            st.session_state.new_status = STATUS_OPTS[0]
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
        
        reset_film = st.session_state.new_film_reset

        new_picture = st.file_uploader('Image', type=['png', 'jpg', 'jpeg', 'webp'], key=f'new_film_picture_{reset_film}')
        
        if not new_picture is None:
            with st.container(horizontal_alignment='center'):
                st.image(new_picture, width=200)
        else:
            new_picture = st.secrets.indicators.PLACEHOLDER_IMG_POSTER

        new_status = st.selectbox('Status', key='new_status', options=STATUS_OPTS)
        new_title = st.text_input('Title*', key='new_title', placeholder='Enter new film title...') 

        selected_actress = st.multiselect('Actress*', key='new_actresses', options=ACTRESS_OPTS)

        new_act_error = False
        if st.checkbox('New Actress', key='new_actress_check'):
            new_actress = '?'
            st.markdown('---')
            new_actress_input = st.text_input('New Actress Name*', placeholder='Alphabet, Kanji')
            if new_actress_input:
                new_actress_name, new_actress_native = new_actress_input.split(', ')
                st.write('Name: ', new_actress_name)
                st.write('Kanji: ', new_actress_native)
            new_nationality = st.selectbox('Nationality', options=COUNTRY_OPTS)

            new_job = st.multiselect(
                "Job*", 
                options=JOB_OPTS,
                key=f"new_job"
            )
            group_inputs = {}
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

            if idol_error or group_error or new_actress_input == '' or new_job == []:
                new_act_error = True
            else:
                new_jobs = format_job_with_groups(new_job, group_inputs)
                new_act_error = False
            st.markdown('---')
        elif selected_actress:
            new_actress = ", ".join(selected_actress)
            new_actress_input = '?'
        else:
            new_actress = '?'
            new_actress_input = '?'

        selected_genre = st.multiselect('Genre*', key='new_genre', options=GENRE_OPTS)
        new_genre = ", ".join(selected_genre)

        new_type = st.selectbox('Type', key='new_type', options=TYPE_OPTS)

        if new_type == 'Series':
            new_episode = st.number_input('Episode', key='new_episode', min_value=1)
            new_info = st.selectbox('Info', key='new_info_s', options=INFO_OPTS_S)
        else:
            new_episode = '?'
            new_current_eps = '?'
            new_info = st.selectbox('Info',key='new_info_m', options=INFO_OPTS_M)
        

        if new_info == 'On Going':  
            new_current_eps = st.number_input('Current Episode', min_value=1, max_value=new_episode)
            new_rating = '?'
        elif new_info == 'Complete':
            new_current_eps = new_episode
            new_rating = st_star_rating('Rating', maxValue=5, defaultValue=3, key="new_rating", emoticons=True)
            new_rating = int(new_rating)
        else:
            new_current_eps = '?'
            new_rating = '?'

        new_playlist = st.selectbox('Playlist', key='new_playlist', options=PLAYLIST_OPTS)

        if st.checkbox('New Playlist', key='add_new_playlist'):
            new_new_playlist = st.text_input('New Playlist', placeholder='Enter new playlist...', key='add_film_new_playlist')
            if new_new_playlist != '' or new_new_playlist != None:
                new_playlist = new_new_playlist
        
        new_note = st.text_area('Note', placeholder='How do you think about the film/series...')

        if new_note == '':
            new_note = '--'


        with st.container(key='film_new_button', horizontal=True):
            if st.button('💾 Add Film', width='stretch'):
                if new_title and new_genre and ((new_actress!='?')or(new_actress_input!='?')) and not new_act_error:
                    if new_actress_input!='?':
                        # Create new row data
                        new_row = pd.DataFrame([{
                            'Review': 'Not Watched',
                            'Picture': st.secrets.indicators.PLACEHOLDER_IMG,
                            'Name (Alphabet)': new_actress_name,
                            'Name (Native)': new_actress_native,
                            'Birthdate': '?',
                            'Age': '?',
                            'Nationality': new_nationality,
                            'Height (cm)': '? cm',
                            'Job': new_jobs,
                            'Favourite': 0
                        }])


                        # Add to DataFrame
                        new_name_native = new_row['Name (Native)'].iloc[0]
                        df_actress = st.session_state.actress_df

                        if new_name_native in df_actress['Name (Native)'].values:
                            st.warning(f"⚠️ Actress '{new_name_native}' already exist in database!")
                            st.stop()
                        else:
                            df_actress = pd.concat([df_actress, new_row], ignore_index=True)   
                            df_actress = df_actress.sort_values('Name (Alphabet)', key=lambda col: col.str.lower(), ascending=True, ignore_index=True)
                            # Update ke Google Sheets
                            if update_google_sheets(df_actress,conn,'actress'):
                                st.success("✅ New actress added successfully to Google Sheets!")
                                st.session_state.actress_df = values_handling(df_actress,'actress')  # Update session state
                            else:
                                st.error("❌ Failed to add new actress to Google Sheets")
                                st.stop()
                        new_actress = new_actress_name

                    if new_picture:
                        join_name = new_title
                        clean_name = re.sub(r'[^\w]', '', join_name)
                        clean_name = "N" + clean_name
                        picture_url = upload_to_database(new_picture, clean_name)
                    else:
                        picture_url = st.secrets.indicators.PLACEHOLDER_IMG_POSTER
                    
                    new_row = pd.DataFrame([{
                        'Status': new_status,
                        'Info': new_info,
                        'Picture': picture_url,
                        'Title': new_title,
                        'Type': new_type,
                        'Current Episode': new_current_eps,
                        'Episode': str(new_episode),
                        'Genre': new_genre,
                        'Rating': new_rating,
                        'Playlist': new_playlist,
                        'Actress Name': new_actress,
                        'Note' : new_note
                    }])

                    df = st.session_state.film_df
                    new_film_title = new_row['Title'].iloc[0]

                    if new_film_title in df['Title'].values:
                        st.warning(f'⚠️ Title {new_film_title} already exist in database')
                        st.stop()
                    else:
                        df = pd.concat([df,new_row], ignore_index=True)
                        if update_google_sheets(df,conn,'film'):
                            st.session_state.film_df = values_handling(df,'film')
                    
                    st.rerun()
                else:
                    st.error('Fill mandatory fields first! (*)')
                    st.stop()
            if st.button('Close', type='primary', width='stretch'):
                st.rerun()
            
            

    with st.sidebar:
        if st.button('⬅️ Back', width='stretch'):
            return 'home'
        
        st.markdown('---')
        if st.button('➕ Add New Film', width='stretch'):
            add_new_film()
        if st.button('🔐 Logout', width='stretch'):
            st.session_state.clear()
            return 'login'
        if st.button('⬆️ Back to top', width='stretch'):
            st.session_state.scroll_to_top = True
            st.rerun()
    
    # Main
    st.space('small')
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Film List</h1>", unsafe_allow_html=True)
    
    if st.session_state.viewing_film_index is not None:
        show_film_details()

    display_film_grid(df, actress_df)
    st.markdown('---')
    if st.button('⬆️ Back to top', width='stretch'):
        st.session_state.scroll_to_top = True
        st.rerun()
    st.markdown("""
    <style>
    /* Container untuk beberapa badge */
    .badge-stack {
        position: absolute;
        top: 20px;
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

    /* info badge */
    .info-badge {
        padding: 4px 9px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        color: white;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }

    /* Warna info */
    .info-want-to-watch { background-color: #2ecc71; }
    .info-on-going { background-color: #f1c40f; }
    .info-drop { background-color: #e74c3c; }
    .info-complete { background-color: #3498db; }

    /* Warna berdasarkan status */
    .status-watched {
        background-color: #2ecc71; /* hijau */
    }
    .status-dissapointing {
        background-color: #95a5a6; /* abu */
    }
    .status-goat {
        background-color: #9b59b6; /* violet */
    }
    .status-slow-release {
        background-color: #e67e22; /* orange */
    }
    .status-not-watched {
        background-color: #e74c3c; /* merah */
    }

    /* Supaya badge nempel di card */
    .cat-card {
        position: relative;
    }
                
    /* Hover effect untuk card */
    .actress-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
        border-color: #004cff !important;
    }
    
    /* Smooth transition */
    .actress-card {
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    
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

def complex_actress(conn):

    if 'actress_initial' not in st.session_state:
        st.session_state.actress_initial = False
    if 'film_initial' not in st.session_state:
        st.session_state.film_initial = False
    if 'scroll_to_top' not in st.session_state:
        st.session_state.scroll_to_top = False
    if 'display_mode' not in st.session_state:
        st.session_state.display_mode = 'List'
    if 'detail_movie_index' not in st.session_state:
        st.session_state.detail_movie_index = None
    if 'actress_index' not in st.session_state:
        st.session_state.actress_index = None

    # Fungsi untuk refresh data dari Google Sheets
    def refresh_data(conn):
        """Refresh data dari Google Sheets ke session state"""
        try:
            with st.spinner("🔄 Refreshing data from Google Sheets..."):
                # Load data baru
                st.cache_data.clear()
                df = load_data_actress(conn)

                if not df.empty:
                    # Clear dan update session state
                    st.session_state.actress_df = df
                    st.session_state.data_loaded = True
                    
                    # Clear editing/viewing states
                    if "editing_index" in st.session_state:
                        st.session_state.editing_index = None
                    if "viewing_index" in st.session_state:
                        st.session_state.viewing_index = None
                    if "adding_new" in st.session_state:
                        st.session_state.adding_new = False
                    
                    st.rerun()
                else:
                    st.warning("⚠️ No data found in Google Sheets")
                    st.stop()
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
        matching_actresses = filtered_actress_df[filtered_actress_df['Name (Alphabet)'].isin(actress_list)]
        for i in range(0,len(matching_actresses)):
            with st.container(horizontal=True):
                st.image(matching_actresses['Picture'].iloc[i], width=80)
                with st.container():
                    st.markdown(f"### {matching_actresses['Name (Alphabet)'].iloc[i]}")
                    # st.markdown(f"### {matching_actresses['Name (Alphabet)'].iloc[i]}")
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
        df = init_dataframe_actress(conn)
    
    if st.session_state.film_initial == False:
        film_df = init_dataframe_film(conn)

    # Inisialisasi variabel kontrol
    if "editing_index" not in st.session_state:
        st.session_state.editing_index = None
    if "viewing_index" not in st.session_state:
        st.session_state.viewing_index = None
    if "adding_new" not in st.session_state:
        st.session_state.adding_new = False
    if "film_detail" not in st.session_state:
        st.session_state.film_detail = False

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
                    <h3>{actress['Name (Alphabet)']}</h3>
                    <h2>{actress['Name (Native)'] if pd.notna(actress['Name (Native)']) else ''}</h1>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Tombol Edit dan Close
            button_container = st.container(key='view_edit_close', horizontal=True)
            with button_container:
                if st.button("✏️ Edit", width='stretch', key=f"edit_btn_{index}"):
                    st.session_state.editing_index = index
                    st.rerun()

                if st.button("❌ Close", width='stretch', key=f"close_{index}"):
                    st.session_state.viewing_index = None
                    st.session_state.editing_index = None
                    st.rerun()

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
        filtered_film = film_df[film_df['Actress Name'].str.contains(actress['Name (Alphabet)'])]

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

        if st.button("Close", width='stretch', key=f'cancel_{index}', type='primary'):
            st.session_state.viewing_index = None
            st.session_state.editing_index = None
            st.rerun()

    def show_edit_mode(index):
        def delete_actress(index):
            # Hapus data dari DataFrame
            actress = df.loc[index]
            pic_filename = str(actress['Picture']).split('/')[-1]
            pic_id = pic_filename.split('.')[0]

            if 'placeholder' not in pic_id:
                delete_cloudinary_image(pic_id)

            df.drop(index, inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            # Update ke Google Sheets
            if update_google_sheets(df,conn,'actress'):
                st.success("✅ Actress deleted successfully from Google Sheets!")
                st.session_state.actress_df = values_handling(df,'actress')  # Update session state
            else:
                st.error("❌ Failed to delete actress from Google Sheets")
            
            st.session_state.editing_index = None
            st.session_state.viewing_index = None
            st.rerun()
        index = st.session_state.editing_index
        actress = df.iloc[index]
        st.space('small')
        st.markdown(f"#### ✏️ Editing: {actress['Name (Alphabet)']}")
        
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
                
            if st.button("🗑️ Delete Actress", width='stretch', type="secondary", key=f"delete_{index}"):
                delete_actress(index)


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
            edited_review = st.selectbox(
                "Review", 
                options=REVIEW_OPTS,
                index=review_index,
                key=f"review_{index}"
            )
            
            edited_name = st.text_input(
                "Name (Alphabet)", 
                value=actress['Name (Alphabet)'] if pd.notna(actress['Name (Alphabet)']) else "",
                placeholder="Enter name in alphabet",
                key=f"name_{index}"
            )
            
            edited_native = st.text_input(
                "Name (Native)", 
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
                min_value=date(1981,1,1)
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
            "Job", 
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


        # Save changes
        if st.button("💾 Save Changes", width='stretch', type="primary", key=f"save_{index}"):
            # Generate clean name untuk public_id
            join_name = edited_name
            clean_name = re.sub(r'[^\w]', '', join_name)
            clean_name = "N" + clean_name

            old_filename = str(actress['Picture']).split('/')[-1]
            old_public_id = old_filename.split('.')[0]
            final_picture_url = actress['Picture']

            # kalau cuma ganti foto
            if new_pic and (edited_name == actress['Name (Alphabet)']) and not job_error:
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
            # kalau ganti foto dan code
            elif new_pic and (edited_name != actress['Name (Alphabet)']) and not job_error:
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
            # kalau cuma ganti code
            elif not new_pic and (edited_name != actress['Name (Alphabet)']) and not job_error:
                if pd.notna(actress['Picture']) and actress['Picture'] and "placeholder" not in str(actress['Picture']).lower():
                    try:
                        final_picture_url = rename_cloudinary_image(old_public_id, clean_name)
                    except Exception as e:
                        st.warning(f'Could not rename old image: {e}')
                        st.stop()
            elif job_error:
                st.error('Fill mandatory fields! (*)')
                st.write(not job_error)
                st.stop()

            # Update data di DataFrame
            df.at[index, 'Review'] = edited_review
            df.at[index, 'Picture'] = final_picture_url
            df.at[index, 'Name (Alphabet)'] = edited_name
            df.at[index, 'Name (Native)'] = edited_native
            df.at[index, 'Birthdate'] = edited_birthdate
            df.at[index, 'Age'] = age
            df.at[index, 'Nationality'] = edited_nationality
            df.at[index, 'Height (cm)'] = edited_height
            df.at[index, 'Job'] = edited_jobs
            df.at[index, 'Favourite'] = edited_favourite
            
            # Update ke Google Sheets
            if update_google_sheets(df,conn,'actress'):
                st.session_state.actress_df = values_handling(df,'actress')  # Update session state
            else:
                st.error("❌ Failed to update Google Sheets")
                st.stop()
            
            st.session_state.editing_index = None
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
            st.session_state.new_status = STATUS_OPTS[0]
            st.session_state.new_height = 130
            st.session_state.new_job = ''
            st.session_state.new_idol_group = ''
            st.session_state.new_ex_member_group = ''
        
        if 'new_pic_reset' not in st.session_state:
            st.session_state.new_pic_reset = 0
        
        reset_pic = st.session_state.new_pic_reset        
        
        # Basic Information
        st.subheader("Basic Information")

        new_picture = st.file_uploader("Image", type=['png', 'jpg', 'jpeg', 'webp'], key=f'new_picture_{reset_pic}')

        if not new_picture is None:
            with st.container(horizontal_alignment='center'):
                st.image(new_picture, width=200)    

        new_review = st.selectbox("Review", options=REVIEW_OPTS, key='new_review')
        new_name = st.text_input("Name (Alphabet)*", placeholder="Enter name in alphabet", key='new_name')
        new_native = st.text_input("Name (Native)*", placeholder="Enter name in native", key='new_native')
        new_nationality = st.selectbox("Country", options=COUNTRY_OPTS, key='new_nationality')
        new_birthdate = st.date_input("Birthdate", min_value=date(1980,1,1), key='new_birthdate')

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
            "Job", 
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
            if new_name and new_native and not job_error:
                if new_picture:
                    join_name = new_name
                    clean_name = re.sub(r'[^\w]', '', join_name)
                    clean_name = "N" + clean_name
                    picture_url = upload_to_database(new_picture, clean_name)
                else:
                    picture_url = st.secrets.indicators.PLACEHOLDER_IMG

                # Create new row data
                new_row = pd.DataFrame([{
                    'Review': new_review,
                    'Picture': picture_url,
                    'Name (Alphabet)': new_name,
                    'Name (Native)': new_native,
                    'Birthdate': new_birthdate,
                    'Age': new_age,
                    'Nationality': new_nationality,
                    'Height (cm)': new_height,
                    'Job': new_jobs,
                    'Favourite': new_favourite
                }])

                # Add to DataFrame
                df = st.session_state.actress_df
                new_name_native = new_row['Name (Native)'].iloc[0]

                if new_name_native in df['Name (Native)'].values:
                    st.warning(f"⚠️ Actress '{new_name_native}' already exist in database!")
                    st.stop()
                else:
                    df = pd.concat([df, new_row], ignore_index=True)       
                    # Update ke Google Sheets
                    if update_google_sheets(df,conn,'actress'):
                        st.session_state.actress_df = values_handling(df,'actress')  # Update session state
                    else:
                        st.error("❌ Failed to add new actress to Google Sheets")
                        st.stop()
                    
                    st.session_state.adding_new = False
                    st.rerun()
            else:
                st.error('Fill mandatory fields first! (*)') # Error disini
                st.stop()
        
        if cancel_new:
            st.session_state.adding_new = False
            st.rerun()

    # Sidebar
    with st.sidebar:
        if st.button('⬅️ Back', width='stretch'):
            return 'home'
        st.header(f'Actress Listed : {len(st.session_state.actress_df)}')
        st.markdown("---")
        st.header("⚙️ Display Settings")
        st.session_state.display_mode = st.radio(
            "View Mode",
            ["Gallery", "List"],
            key='display_mode_radio',
            index=0 if st.session_state.display_mode == "Gallery" else 1
        )
        st.markdown("---")
        with st.container(key='review_filter'):
            st.header("Review Filters")
            show_actress_watched = st.checkbox("Watched", value=True)
            show_actress_not_watched = st.checkbox("Not Watched", value=True)
        with st.container(key='Favourite'):
            st.header("Favourite Filters")
            show_favourite = st.checkbox("Favourite",value=False)
        
        st.markdown("---")
        st.subheader("Management")
        if st.button("➕ Add New Actress", width='stretch'):
            st.session_state.adding_new = True
            st.rerun()
        
        # # Tombol refresh data
        # if st.button("🔄 Refresh Data", width='stretch'):
        #     refresh_data()
        #     st.rerun()
        
        if st.button('🔐 Logout', width='stretch'):
            st.session_state.clear()
            return 'login'
    if st.session_state.adding_new:
        add_new_actress()

    if st.session_state.viewing_index is not None:
        show_actress_details()

    if st.session_state.film_detail:
        show_movie_details()

    if not df.empty and 'Picture' in df.columns:
        if st.session_state.get('search_reset', False):
            st.session_state.search_reset = False
            st.session_state.search_bar = ''
        st.space('small')    
        st.space('small')    
        
        search_container = st.container(horizontal=True, vertical_alignment='bottom')

        with search_container:
            search_query = st.text_input("🔍 Search actress by Name (Alphabet / Kanji):", 
                            placeholder="Type name to search...", key='search_bar')
            if st.button('Clear'):
                st.session_state.search_reset = True
                st.rerun()

        # Filter DataFrame berdasarkan status
        filtered_df = df.copy()
        filtered_df = filtered_df.sort_values(by='Name (Alphabet)', ascending=True)

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
        if not search_query and not search_query.isspace() and not filtered_df.empty:
            st.write('')
        elif search_query and not search_query.isspace() and not filtered_df.empty:
            search_lower = search_query.lower().strip()
            search_mask = (
                filtered_df['Name (Alphabet)'].fillna('').str.lower().str.contains(search_lower, na=False) |
                filtered_df['Name (Native)'].fillna('').str.contains(search_query.strip(), na=False)
            )
            filtered_df = filtered_df[search_mask]
            # filtered_df = filtered_df.reset_index(True)
            st.info(f'Showing {len(filtered_df)} results')
        
        else:
            st.warning("No actresses match the selected filters.")
            st.stop()

        if st.session_state.display_mode == "Gallery":
            st.write('Under Development!')
            # try:
            #     clicked = clickable_images(
            #         filtered_df['Picture'].dropna().tolist(),
            #         titles=filtered_df["Name (Alphabet)"].fillna("").tolist(),
            #         div_style={
            #             "display": "grid",
            #             "grid-template-columns": "repeat(3, 1fr)",
            #             "gap": "8px",
            #             "width": "100%"
            #         },
            #         img_style={
            #             "width": "100%",        
            #             "aspect-ratio": "1 / 1", 
            #             "object-fit": "cover",
            #             "border-radius": "15%",
            #             "cursor": "pointer"
            #         } 
            #     )

            #     if clicked > -1:
            #         index = filtered_df.index[clicked]
            #         st.session_state.viewing_index = index
            #         st.session_state.editing_index = None
            #         st.session_state.actress_index = index
            #         show_actress_details()
            #         st.rerun()
                        
            # except Exception as e:
            #     st.error(f'Error Generate Image: {e}')
            #     st.stop()
        else:
            
            for i in range(0,len(filtered_df)):
                index = filtered_df.index[i]
                review_text = filtered_df['Review'].iloc[i]

                if review_text == 'Not Watched':
                    review_icon = '🔴'
                    review_color = 'red'
                elif review_text == 'Watched':
                    review_icon = '🟢'
                    review_color = 'green'
                else:
                    review_icon = '⚪'
                    review_color = 'grey'
                with st.container(key=f'actress_card_{i}'):
                    with st.container(horizontal=True, horizontal_alignment='distribute'):
                        st.markdown(f'###### {filtered_df["Name (Alphabet)"].iloc[i]} -- {filtered_df["Name (Native)"].iloc[i]}')
                        if filtered_df['Favourite'].iloc[i] == 1:
                            st.badge(f"",icon='⭐', color='yellow',width='content')
                    st.badge(f"{filtered_df['Review'].iloc[i]}",icon=review_icon, color=review_color)
                    with st.container(horizontal=True):
                        st.image(filtered_df['Picture'].iloc[i], width=120)
                        with st.container(horizontal=False, width='content'):
                            if filtered_df['Birthdate'].iloc[i] == '?':
                                st.write('🎂 DoB : ?')
                            else:
                                st.write(f'🎂 DoB : {datetime.strptime(filtered_df["Birthdate"].iloc[i],"%d/%m/%Y").date().strftime("%b %d, %Y")}')
                            st.write(f'👧 Age : {filtered_df["Age"].iloc[i]}')
                            st.write(f'🌍 Country : {filtered_df["Nationality"].iloc[i]}')
                    if st.button('🔍 View Details', key=f"button_{filtered_df['Name (Alphabet)'].iloc[i]}", width='stretch'):
                        st.session_state.viewing_index = index
                        st.session_state.editing_index = None
                        st.session_state.actress_index = index

                        show_actress_details()
                        st.rerun()
                    st.markdown(f"""
                        <style>
                            .st-key-actress_card_{i}{{
                                background-color: #1D546D;
                                padding: 5px;
                                border-radius: 5px;
                            }}
                        </style>
                    """, unsafe_allow_html=True)
                st.space('small')
                
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