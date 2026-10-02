import sqlite3
import requests
import streamlit as st

API_KEY = "508af0e4f8734511b69f6562d4ae9539"
DB_FILE = "moje_hry.db"

# --- DATABÁZA ---
def inicializuj_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS MojeHry (
                id INTEGER PRIMARY KEY,
                nazov TEXT NOT NULL,
                zaner TEXT,
                platforma TEXT,
                stav TEXT DEFAULT 'Na rade',
                hodnotenie INTEGER DEFAULT 0
            )
        """)

def nacitaj_z_db():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nazov, zaner, platforma, stav, hodnotenie FROM MojeHry ORDER BY id DESC")
        return cur.fetchall()

def pridaj_do_db(hra_id, nazov, zaner, platforma):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT INTO MojeHry (id, nazov, zaner, platforma)
                VALUES (?, ?, ?, ?)
            """, (hra_id, nazov, zaner, platforma))
        return True
    except sqlite3.IntegrityError:
        return False

def uprav_v_db(hra_id, stav, hodnotenie):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            UPDATE MojeHry
            SET stav = ?, hodnotenie = ?
            WHERE id = ?
        """, (stav, hodnotenie, hra_id))

def vymaz_z_db(hra_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM MojeHry WHERE id = ?", (hra_id,))

# --- INICIALIZÁCIA ---
inicializuj_db()
st.set_page_config(page_title="Herný Tracker", layout="wide")

st.title("🎮 Herný Tracker (RAWG API & SQLite)")

# --- 1. VYHĽADÁVANIE HIER (RAWG API) ---
st.subheader("🔍 Hľadať nové hry")

col1, col2 = st.columns([3, 1])
with col1:
    hladany_text = st.text_input("Názov hry", value="witcher", label_visibility="collapsed")
with col2:
    hladat_btn = st.button("Hľadať v RAWG", use_container_width=True)

if hladat_btn and hladany_text.strip():
    url = f"https://api.rawg.io/api/games?search={hladany_text}&key={API_KEY}"
    try:
        odpoved = requests.get(url, timeout=5)
        odpoved.raise_for_status()
        hry = odpoved.json().get("results", [])
        st.session_state["vysledky_api"] = hry
    except Exception as e:
        st.error(f"Chyba pri pripájaní k API: {e}")

if "vysledky_api" in st.session_state and st.session_state["vysledky_api"]:
    st.write("**Výsledky vyhľadávania:**")
    for hra in st.session_state["vysledky_api"][:10]:
        h_id = hra.get("id")
        nazov = hra.get("name")
        zanre = hra.get("genres", [])
        zaner = zanre[0]["name"] if zanre else "Neznámy"
        platformy = hra.get("platforms", [])
        platforma = platformy[0]["platform"]["name"] if platformy else "Neznáma"

        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        c1.write(f"**{nazov}**")
        c2.write(f"🎭 {zaner}")
        c3.write(f"💻 {platforma}")
        if c4.button("➕ Pridať", key=f"add_{h_id}"):
            if pridaj_do_db(h_id, nazov, zaner, platforma):
                st.success(f"Hra '{nazov}' bola pridaná!")
                st.rerun()
            else:
                st.warning("Túto hru už máš v knižnici.")

st.divider()

# --- 2. OSOBNÁ KNIŽNICA ---
st.subheader("📚 Moja uložená knižnica")

ulozene_hry = nacitaj_z_db()

if not ulozene_hry:
    st.info("Knižnica je zatiaľ prázdna. Pridaj nejakú hru vyššie!")
else:
    for hra in ulozene_hry:
        h_id, nazov, zaner, platforma, stav, hodnotenie = hra
        
        with st.expander(f"**{nazov}** | Stav: {stav} | Hodnotenie: {hodnotenie}/10"):
            col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
            
            novy_stav = col_a.selectbox(
                "Stav", 
                ["Na rade", "Rozohrané", "Dokončené", "Odložené"], 
                index=["Na rade", "Rozohrané", "Dokončené", "Odložené"].index(stav),
                key=f"stav_{h_id}"
            )
            
            nove_hodnotenie = col_b.number_input(
                "Hodnotenie (0-10)", 
                min_value=0, 
                max_value=10, 
                value=int(hodnotenie),
                key=f"hodn_{h_id}"
            )
            
            if col_c.button("💾 Uložiť zmeny", key=f"save_{h_id}"):
                uprav_v_db(h_id, novy_stav, nove_hodnotenie)
                st.toast("Zmeny boli uložené!")
                st.rerun()
                
            if col_d.button("🗑️ Vymazať", key=f"del_{h_id}"):
                vymaz_z_db(h_id)
                st.toast("Hra bola vymazaná!")
                st.rerun()