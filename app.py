import streamlit as st
import pandas as pd
import time
import io
from openai import OpenAI

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Productcaster · Translator",
    page_icon="🔺",
    layout="centered",
)

# ── Branding & Styling ─────────────────────────────────────────────────────────
# Productcaster palette:
#   Charcoal text:  #2d2d2d
#   Red accent:     #c0392b  (darker) / #e04e36 (mid) / #f05a35 (lighter)
#   Light bg:       #f7f6f4
#   Card bg:        #ffffff
#   Border:         #e2e0db
#   Muted text:     #888580

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f7f6f4;
    color: #2d2d2d;
}

.block-container {
    max-width: 800px;
    padding-top: 0 !important;
    padding-bottom: 4rem;
}

/* ── Top bar ── */
.pc-topbar {
    background: #2d2d2d;
    margin: -1rem -4rem 2.5rem;
    padding: 0.85rem 4rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.pc-logo-text {
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f0ede8;
}
.pc-logo-text span { color: #e04e36; }
.pc-topbar-sub {
    margin-left: auto;
    font-size: 0.78rem;
    color: #888;
    font-weight: 400;
}

/* ── Page title ── */
.pc-title {
    font-size: 1.6rem;
    font-weight: 600;
    color: #2d2d2d;
    letter-spacing: -0.025em;
    margin: 0 0 0.3rem;
}
.pc-subtitle {
    font-size: 0.88rem;
    color: #888580;
    margin: 0 0 2rem;
    font-weight: 400;
}

/* ── Section label ── */
.pc-section {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #b0ada8;
    margin: 0 0 0.6rem;
}

/* ── Streamlit component overrides ── */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    border: 1px solid #e2e0db !important;
    border-radius: 6px !important;
    color: #2d2d2d !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #e04e36 !important;
    box-shadow: 0 0 0 3px rgba(224,78,54,0.12) !important;
}

/* Primary button */
.stButton > button {
    background: #e04e36 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.75rem !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #c0392b !important; }
.stButton > button:disabled { background: #e2e0db !important; color: #b0ada8 !important; }

/* Download button */
.stDownloadButton > button {
    background: #ffffff !important;
    color: #e04e36 !important;
    border: 1px solid #e04e36 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
}
.stDownloadButton > button:hover { background: #fdf1ef !important; }

/* Expander */
div[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e2e0db !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}

/* File uploader */
div[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 1.5px dashed #e2e0db !important;
    border-radius: 8px !important;
}

/* Progress bar */
div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #e04e36, #f08060) !important;
    border-radius: 4px !important;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e0db;
    border-radius: 8px;
    padding: 1rem 1.25rem;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #2d2d2d !important;
    font-weight: 600 !important;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid #e2e0db;
    border-radius: 8px;
    overflow: hidden;
}

/* Alerts */
div[data-testid="stAlert"] { border-radius: 6px !important; }

/* Divider */
hr { border-color: #e2e0db !important; }

/* Success text override */
.pc-success { color: #2e7d52; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Top bar with logo ──────────────────────────────────────────────────────────
LOGO_B64 = "UklGRu4eAABXRUJQVlA4IOIeAABwJAGdASqwBHYCPkkkkUYioiIhIPR4iFAJCWlu4XdBjwgB2Bvxd6fDcLvT+SOx384XhT/Afmr/meAA/UTpI+YD/nemV6E/QA/WD//9gp6BPmtf7H9sfiM/dH9mcxl8q/7nto/vH9v/HP1L/HPpP8P+XX919yfIv2kak3yn72fuf7l6Q/sF44/MTUL/Jv6n/sd8hAH9g/AJ1bvCPsAeO/+p8Rf6V/lP2i+AT+Qf17/s/3L8s/pq/zv/l5+P2j1EwdmNuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj61lTpjUzArE/U8boj610R9a6I+tdEfWuiPrWZTwAvW0OnADEITZxua0Ot7+M1bPOxqOEs4SZkwdNV5zrB+0wK55raiJ4ox01byB9J7wCYLBbOFqX+aQxkart1IINjC8OI8R/TTVqiG7zaYwEne/axxJeImCh1jCv1o+P5yRTTZeTB72TVm+9FqYf9C1Inq9lsCIbqjADQ4GQkeIJFu4kuDQpzVVwKLwF7WKKvPFEq6yFVNUPKUjfForonwMWZ0jm6CyBiOEPSX2szcwL4roFm42PUx0Qgn4GAQ5roHFeALwt9AhGo93V610R9a6IuWsjORDzMo5EqGGgpjRdHko/whSG+2SBiALIwlzcBCXW7OrrV6wTfrGQYV04RW8l37VRq6H5DFWnueUGSrf7K1zD86lVpSzNlK/4jz5mgz2IgMPDZL5x6fWs/e30cq7wvmicWvYiq8adaa1cRbK4JMSrSv/PrsD4XkbwmM0L57jjf4dYAxOcYclwvXEgz6YFazx7Mi2gGBnjvh5QTCJbk4j3dXrXRH1rN3bIvuC6DUmPDrSrBI1r6PF9SXI/8gjnSKL1JinaE+zI64TX6dynPmzTvE05y7U6McRwtc28ultAP3QEqCgbtnYIZ689H4zIUq8+P2kUMy59ieliPDEWhTu+My9WgTLLQVWxjHjrk7L+dZUctMvlTwoNFr8Yuj184j3dXrXRH1rN3bklcXLm9BHSnqLIBySa48xENZmIl41NN1HXZjRr80bSVzhWZ7jslZeDVFpY/pbZiJl7jqoz6MvEXZl+x7UmkCScim+pcYR6Ngbu81/qix+XfMTihFnssAauAh8HoniI6h+4MmVxdtbgBljr4pBBm1MNURKcOG7R7eqI55ltZutSnVS1CbnphtmcgIxIx2l1k9lxSlyD4vkg4Ukhg+tdEXLaAYGeK6/Kthe/0lSwbpG1UwdQOV9U21fsws0vXxIpbhP0T7OldfXGnzLUg56yQ+xHuUOh8fBJAsN3OWQgl/MKkcbw1XY3sfGRdwCQBBj6/N31ceL6+VvQwMolHv9MGzBjJKCTkiPB6Jk282jp6mUFhmGSzNsmHDVBNr5fXBsx+bqNflqAw4YsyM0EBLduXJsGrkXiIF+XzlHsuP3buexKDTYCsg05Hkvd2fJupCL0WgRfOI93V610R9ZkLAHzUV93sVtOMuU7TozNKw2ciMgHrvAoEu9vPzdB7zcjiE3R7ZwXSTYrd80C2Ss0S5IGe9qJxzIXyC4fkztRONrHM+URw/9ypjtzhQLxlFcjI1mLJv25GbKupsKn9cDIFV/VhObM0b+tmbCTsSsznDCmavC0TvdxLX32YPowXwAzjEiaismWcQJGWTJhC+4YPrXRH1roj6164+tdFR7lPza6TpyyT1RUcpquf0mr7ur1rpYiPd1etdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roj610R9a6I+tdEfWuiPrXRH1roWAAD+/+TfAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARvN+rVSAzsHlAMluk+DdVrZvuYCBO39I/obP41YQzGfiYX/xi/8dHhWF6EQymEGdnNFfMxA+UOO98/us2/qckAHKz6q1Me9SsRo/Zwz+sGhjF8qfU+8ZnVXHk3osK4lfol14JVoXQ0UZwTKcyhUAuE4ZCBOlWGx3jPGZ1xLWjWiyqiis7MXnQlYNDJweAn75AcMQKMoaRSGo+/5ieYD2RkFERiApHfgZCHNB4vqBndlXSUry1Uvbq/Z4khLFhB9EYwppicbZRq0lALDj7wOSTkBtiu0VjtWypLf7GvmwDbfD3yHY0NS5fT+S1Xdc3AftAgdmpEe4Yy5KjIwkuZ98+80Pu80gSEmYzMAEfaLDBF2KgxBDdVKslD2PuXiziN/OgGjKDcCZ+BO36kAgqLwtlxZv9RrEX/VWf8cnpzZdttlJtVMbkAmhvg0U+56QzYgGM67eS/Z1VipLW6Zw1DY9GTzkzKzTXDLq0zq9tm/NK1+YNbAOn4JmRL5BAWPOrnBBUapUsQEW3hJYvtVzIoxR6GS/EhH5CeuPq17whcJZPc00njnM/qNfbO9Kq402sT1owDax8Qdhi9v9LrXQmeXfHq+FXFLCQRQJICdjkxeBn0Nai4lpj4QPSi5Da3vGrz7kQLNmpFLwv6RdL+JeyUkwWiILLzKRGEkzdgThc1inrGVpFFu33iHkntIyZm6xd23A7/DJyQmxuQVjb/mIF0VUO6FgElLj8BB+CQBpA/3k+HlV3/Ark85WH3sVGIpsT3KTJzTMHd2rmHhMLrKSPrHDXtV+tPNPZPpPPQyT1R8GUpKTB7EG3izvuEqFAMnPBV73V6B0scf91uQn4Pd633eWoziHVKEAVQp/NElC2191M4Cu3WjloDPb51LLq39nwrz6HNJR8yov+N0FDWjDTIjeES0mHPICnju66o3u4ifgt2uS6xW9cCoDyYw7Lt5V9S+bNd8eVokHiSruP5PLP9pVUCOIC8IHA9vC4r/ZGEEJEsyoYkDg4uj3DeJp1mhvCu9YP/pGOGMZrYc8fUehcwirDbbic4lcylPQWIcLy2UONNxgt/L7VNs2oUOKYUaa7lCUKCzb7DPQpmTpUfACsW7yWoD0hFEWP1WRfvAPqTpQv4KaI4Et4ysyPhPtbbvq25eXXjbEEdS9A31xu+/CFUESIchBbOAQgjB1YO5qAqBQH5ABWwm/IcDGmkpN7ULZP2M76ALf0UNXmoUH9j+pkm/xPyOXFprRUNEo2GMPHvtV2nsaT0bqS+D4EBu0uL1SglFAdl28q6O8Vm2mzs+CQb/csx0DbL7KLwuCFRo0XUshBBA7sCOynkHn+73M3GF45VsgTjk3jqy9jpPrdrebbU4CWygQmzDWqUvXhJymHCHEk8pJwScndrKfVHawU21mQeS6zf471CqUQ0FX4C0jzbo6LALqN0jdW9+zd/y6xZl/ohBSMULkxR1iEr5wZLWyPvrlhmNBCfn8hx2Nm6KZ70o9K1gqsypjV78Z7/GCjwk7VPAOWwkp4eXJN4xrpc/zSTsWJDzJ8pjlOnjH0/qPtz4N7HaA7MrSRytLvRQm9oJ+YbvMMopUhTaPAA70WNpBjdYirNEUUFwnevMjHQNmEGaNu3W1FyBRjHF1Xl1ECs4bE8ciAnXqrXi24rc1LxPQwtYlRq4xYNOYzgC9nP5HYqzdQ2pSy8gskjwCk05uM7t+YuITcSDEdITvpXCty4Gebggn9uty+HNcHaTLm23IiH84h9KSJuWA4fjg36YQpad9K7EiPu9phdqDU4bQxzBgXmTAB+u6QmKROGiUR1l12YakK1yP0l7QSb8ks5s2oO5td7zNtZwuCVnTGML9MXMqQhpj8fvRKPJuqLJCA/JD4Q0x8xvlvS+3jpxfDUKFSHDvrGtzsZ2tlA/YjUmjR63pRGkEhihCvH3YOq2gi3EPFksDBAFEfFqUMq5vDsh9aYcMJ+pSLaVpw0wW/N/gU8ITImYo90o97UquxkrRgMLUF7K90SY3eumRgEmJkC9Kv6Al56oGG+CBaE42kQfRgfUpVHrp0LRooaQrP8MrG14yoTtrR5tkzrUEXSmJVeJ6pmFdcKbKv4RhRYj98WhsTLlTyajU+GN1y9gFapimbOg44l900G4YKJ2JUWsL87CzZVEdh7Z64511y1Q63od3CrJb/6bMoeLmzLpAHrT+D6bbumOSWPRsp/PJhYribjHm0VvmCpm5Fb5fm/gx1er2hgJt0O/CKU/elg931PcIOzK12ePAoUt6t9A+muMolTtRNuDwYWQn1zHZ7hGlsZ2X2tAgtdNX1XkkCvXYRlNnFZkcXYZ7BuFaTztbCS+/PTDe3ZCqHjF/7l/ewqiYoB0z58LqjT0AcUjU8ji2sgYRWQwAMoejdcrY6abm5aPo4KVBMJsfB3oQYEOM654pRzUTaFmEtYvrQ5Pg2KOESAqNqa0DZzXha0QGxOINwrVQR01kTbdy3EL7mYnmynrsH2kgYhT0lFwhPi3HhfQu10Oc8z61L5s2vcp+/jepaHkkjHwzGAFKhUlNWil5xWHzPZqP/I3RHhJlwekv2Mmzmb+trR39kHFuz32Ukm8krhuekliiziBYsa3t5hwZ5pLYZKlN/lF5LoOoNs8rN0E6QJh/4iJ9+oFDi+xfOmQSrxbctakynHGcNjOGl7YF9wdXDRAzOepTbSFUSTklfnT/dPdcWniiktMqIraiugo0XjmSbQrKvYXSOdk3kfbNhVZ5xeMr3yb3AHTCFzlf+bIMPnC3SrPZstV5qKDxt8ECdi+LIoA4oWIWAzNFNSvC0Lstj9rQ+U4i7lsBk+lSwTKyAgoyhfCWxf07j5Kw+CCfOfet5s8KG/U/M/oPdLpo7Nn3k2JLL7YOZz6D0PBSx3jLrFphMOYSBGzEtZri3Kog5IMWaWUhdcZNzzeYeFvnZoWbijpj1KiZt1XMz3JMBOoo+6hVZ8bBrhxNsStnd9xe/uRCF+SEWD0D3BL7q0XCIeJ6xqSmK7uyn/zcO+lbiW3aNbT5GXeZM80Ogw2DbL4zaZkwl9/O63FCvwBw+0+cUvylvSUidoQ4C0T/l9gC0/5/NPBibH8tUFwajQOIl9mJwEQYScunN7Y6UOvMdVZkCnIt+wAVzWYolv7tsPgw3Ep2FzsPtOKldAQlGXhqXwKyLR6bzJrLLifN7DmGXyxM3QCLLw49FbqOCvhn9X7OfdtvPNSX9rIfFLoGcvTgHCnjNN8DpdVtRZ/tK2Ji3vsED28EBemRB8ZYO68ojOrccXl029WymY/WSBQFsotLVGY6hs8cLCXiPQSvlROmPrD3zZrJ8Px5bi6XjmqFqvm5X38nOOjjDjRBiwaSSh74ERrLL3a21t/y4HWeKisCn5muyRSG92aFY7uzifhGevMOSe+EHsuk+fTKnmZuXhMj2oWYM5bUcJmKT2q6eBiJ+X+ZSo2fIL5mHSN36jYmpWKw15EtV9dXd8APUg0NtzDKd7W+10tIfpea3gqOTlvPf0KqYma/zsSc+nHTlrMF1IOT31HDQL3hCzC3bDk6k0Sn6hpgGwxo+PnsQrmoqX5vKqAwA/7rBFs/aSLCK9qz46sx2m7le9GfJAACU4WdEPK+jVslG2FLpW1Rzd/0Ae9+p/mmLk1/P8If7kV2O5akYo0ttJImJtGHB40xJfKTQXfSqo6OWdbolRwKkKhhvAWSAntw3ATcI5ptPtHctk08Ox4B/Xq3W/ddgb927qQN3JyuWqsN72OvxrnvVnbRRc8JiZSm+OozoVQANPMu7HVagdHNjuBLnzSP/oDATaqgfkj0S6P9LkxR9cKjLGcJzFD+8ZcZE0ILoNRA6msct1iubkpMgcszDygakT7WcR69z9WYkJKNg3CoxO2p/5ctafJlzjh971mi8IJRhpK1uR0AjJk1ICbjHbswU52u2IPI2OsPBsVNVvifLLTDE7Hc4fUUVZg6FAw385ya6vjs9GlqmvJykCnD92AD6FQZ65bW0Ef3vZo22RbXsYvN89rIRdjaG6ElQWD6fT7BmhBVTF+HEmUauhLwnQ0v9JkA4OSCkwYO/ljIat9R5iw5pwTvIfDcOFz3pvwoEh4BEFuHBfmkitlw6zdCKrTOHCjwVBDUixXeJfq+4QxKp5wpXRxzUkaEcXedwOZNT/YqANEnrQ/PVr7cMwt3BfpAEcphodfEiEUibqrTf47SgnON2PCQZ2vu1MUaLDTTgjtlrOu5ydGZEyRme/+tmtxCt76dNZghwCPp+E9r0+Gi8iTke+PYP+eyKTDuH9qUOQ+AhL9z05JYA0eu/nY06GjyofHLmF8Hv6ZV8V/xDKTvmOCBmSJUSSF76aOHJGVqRFoumCJThymI5ZS4C2V46O7ri2eFoJXBC1IiriE7FrO8scWbhx8InF+ckta+cQOWhZVzhf9upJqe4jfiuLD9Jv+6AibTbSTGQUnadXNrR1Z/5+q71xWk/vo/I9QiSlEEaT5//mtPd1jzxhlYQraE+4n6hVQoSF7VtXpn/43tbyoCiB7wU9BuX5NMZLqAB+DzTxHiHvBUdHsvqyOYfXVXZLmhOoJu90Xtnz9CHRjqQsqzqSkdTjUDvnc8mdks/TNlzHrCoW557o8+jcTHLH7fzDT3aLMEbgUxjr4LDL17nQV9ZkNof9Mmijwqjcz5S+NwWSJVH1GgX1S0prTHVnnpoXTR9oIyVgIa4xKNkb/9cpEQkGIDaCX9y2hO7zSY2SVdKsEvlaW6rBX1gVLdkRUEO3BVf2klL3azvFYAHI3U+DoJoKW24AoW75V5GM+otZe3uxEB0AH1peQkBbNjaRyps3xkt7suQljCOSYqsvTzlAS5200cKGb3UBlkGra0RDD8D5S5kgl2DaeeAHwS93/W9qEC44qdXcV4rD8W3ac0KQZY92P4ZVK1nBmOCnALmDbcGGZUYiRkoLrLciEdVeKXggIZDfVkx6QvxjUhPMFjhDKu3iJrwJHnT3vcRi4WabGd9vuzwx7TSYNDcOFCDqjevNzajLdaNY/1SdiBVpSr+/8wjibIkezIlUUpRUuVfRHpR7mQM+wf7wsLlYoPTE/K/UCVzleQ/b+qVuJdDxNF5LA1Wtim5NWTdREgZdJoPrLDU3kUOYQE3OJDqz/CDuPUjpk0HhSQHfDiM5FrwLA7Qd8ElVeqAjoE787zUic5RIQdMW2HPYkKp4S7n6E2VS/Q5BEW8m3e4mn9xOqLRXwtsqWHHuP5U1MgG3+CNDfWJjlFstTdRqKuzuA8xPXRw9tfEhuNoeJsRfFO4a1g41NrabpB6QBlsZ5rWvCWSGD+kfZEY0vdLsjhUil7EGDPZvVcHB9l6fuGu9KToC2iGyJvuxwHsL2xVInAbRFwE72Gi7e75mATXPhljVTSpozf+QHvYHxKFHio4rmvTsfLfEGqSmLvqeoFnx/J61LHOn4yH/Iwvt2nm9Pcw1sX3Ctd+vVs+UdGHv68BKTlfcpbQ4+BqTApbkv9LYBhX2muHXnWeo2E8vFeazbSOP0Nv/8iEjx9ovHt1Qi7MiC4eDjVLG8kXmhsHQx5hj/xpwIkDW8ZBArmRA8/DSwfMF9dWtnTGkCNA+Yg9dTJPIdIWCcVs4sgN6XXdUmCY5haCYaEsBCrWc3T7u2Mb325ZE4J4Q+uVydiXNh0ctmowluvlF1NplbMUfteLyuV6t2YddKIl/x98YRn2Z7WawWkAsX4kK+RBYYOAEO/jQrbTUieQc8ghDrPCw1sD/EHC592xpTxHLk2KajblOo+lGHmcekufYXXwsz3b/xDjlqzpvYz+D5az1h0m4ykktNoI7OrbWGLLrkJfA86FfiXI9vvjV1KR1Q4QoiCtU9HJ//2jceZ6Ox7wSAVg3Ag9kHy6RcijO8afU6l6W4fFMLjc2tDCp7njXMWE1bswX3cn1enK5/LSTJwmo0jjXN3Y4w8sY425cgzBV6wPcMceu5Fur8FwMx3IIXRtZqsIt7FZ3grGok2XJ3Icc4PkAjCm0Ugw4jDi+M5doKJ4L2ijhgeYbH/5m+3x7d/APhExku3gfNrMceL/yjzgWdRs4/55X3P+VHpuG3IWM5PZm/utviC3i4nWon/clnyF1ilsX9o/5gRgE2YTx9qiuKQE19J0OUsjWGATglrYwgPQ+2N/M0S7+dV/VN/6VIaTX38LHF7+sylpuowz98Ia0EbFMO3qfaXa0hTdWaiyVhb6juZYqRidTpcXr8PTAuyYk//RwqtHdcRhEVUCNuXojInvj5cqj71GoI9w3Wcb9haF6yK2x8zkzvg614VzC+QvGfiI77E2Z0imBufbmM/KYJRo0oWBfS5VHeR13bIsXNDPaA8R9zNPgK5EsHQsyM6wXVQWOd1dwDZTYjdbvOyNby1a+DOs1qmPzjK4h4gnj5UgAwSQ3iDDNTIQb/IBFjNWb5IsDYmdTMsFQOrLIKV483JeTti9Zso+apgea5gd8fsQteYWaCS01N+Oyvbuj0VuHkOk+RnjLH/tl5WTGHvlwfDIprywzUyCR5/wWdri32syb/WBnE77Mox/Vjwmvi6aTRcpQ3z4qJ5aEDurOyP8csUm9e1+p6hXPno6iANg0Tpsmqw/1D90DtA1vgrqBlsKqtBL2oNKfhMNg16r4Fm2UPX7xfLGmpziJt6DbwYlJQBJ3sbzpLsOtw+rHGUmEeVWC2j3vIxWdGI+0f+ix/476TqIgpL7LRhUBCWj9qWBYwGont0T9xzMO83ySYOOF4l9HdrIr0AQzX63pOw53wUBbT42hBwQJl3HSifbOg5AD4fQHPsFlMMqoiJKpAE7NwxepUktwPCWfZvXqKhPFqdPg8Wz40OwkmuPhD5NFVZyBsR88AToJPlSuPt4NsLxk8nIoMbKAipgp5qQgNtY7kc7LgEqR1hSAoZHJsQC1Z1Rg6URQVgWcDLYBBpTy4WRxm5tNOGFPbOni/DXGB9iD92TB9xK2jg/xW/r7qVAEwFmSF2VSGPVdk8sFVOVJTMRNPSI2RBvo8aiAm0dZFeLzNisBJNysGAQWAf5dNpFO5dQcHS2m/7qh/sHbT57uo/OGm8DFRUBWW2RlgqItIFLTny86YqHTDpi5UDlvzRzSvDzCnToSTSiQKw0oYsZ7NZqq5V+VZtNa50G09Qx+Fj9iksAT8vIRktmpFn8ZVG9UMzpz4vKAm+SqP6tRhjxFRtbfMiTiORPY9GF8Co71su6XIW9/in7V+3FFC+RqWT1PXRb60AfobmVajhr0BrAcXIfc9tUnQVLT7LmXTTclaKsJb6bylQzCC+cvbQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

st.markdown(f"""
<div class="pc-topbar">
  <img src="data:image/webp;base64,{LOGO_B64}" alt="Productcaster" style="height:28px; width:auto; display:block;" />
  <div class="pc-topbar-sub">Description Translator</div>
</div>
""", unsafe_allow_html=True)

# ── Page heading ───────────────────────────────────────────────────────────────
st.markdown("""
<p class="pc-title">Description Translator</p>
<p class="pc-subtitle">Upload a CSV · translate product descriptions with GPT · download results</p>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
LANGUAGES = [
    "French", "Spanish", "German", "Italian", "Portuguese",
    "Dutch", "Polish", "Swedish", "Danish", "Norwegian",
    "Japanese", "Chinese (Simplified)", "Chinese (Traditional)",
    "Korean", "Arabic", "Hindi", "Turkish", "Russian",
    "Other (specify below)",
]

DEFAULT_PROMPT = (
    "You are a professional translator. Translate the following product description "
    "from English into {language}. Preserve tone, formatting, and any brand-specific "
    "terminology. Return only the translated text with no explanation or preamble."
)

MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

# ── API key from Streamlit secrets ─────────────────────────────────────────────
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error(
        "⚠️  No API key found. Add `OPENAI_API_KEY` to your app's Streamlit secrets. "
        "See the README for instructions."
    )
    st.stop()

# ── Session state defaults ─────────────────────────────────────────────────────
for key, default in {
    "results": None,
    "errors": [],
    "running": False,
    "done": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helper: call OpenAI ────────────────────────────────────────────────────────
def translate_text(client, text, language, system_prompt, model, retries=3):
    prompt = system_prompt.replace("{language}", language)
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content.strip(), None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None, str(e)


# ── Step 1: Configuration ──────────────────────────────────────────────────────
with st.expander("⚙️  Configuration", expanded=not st.session_state.done):
    col1, col2 = st.columns([2, 1])
    with col1:
        lang_choice = st.selectbox("Target language", LANGUAGES)
    with col2:
        model_choice = st.selectbox("Model", MODELS)

    if lang_choice == "Other (specify below)":
        custom_lang = st.text_input("Specify language", placeholder="e.g. Catalan")
        language = custom_lang
    else:
        language = lang_choice

    system_prompt = st.text_area(
        "System prompt  (use `{language}` as a placeholder)",
        value=DEFAULT_PROMPT,
        height=110,
    )

# ── Step 2: Upload ─────────────────────────────────────────────────────────────
st.markdown('<p class="pc-section">Upload CSV</p>', unsafe_allow_html=True)
uploaded = st.file_uploader(
    "Must contain a `url` column and a `description` column (case-insensitive)",
    type="csv",
)

df_preview = None
url_col = desc_col = None

if uploaded:
    try:
        # Read with explicit UTF-8; fall back to latin-1 if needed
        try:
            df_preview = pd.read_csv(uploaded, encoding="utf-8")
        except UnicodeDecodeError:
            uploaded.seek(0)
            df_preview = pd.read_csv(uploaded, encoding="latin-1")

        cols_lower = {c.lower(): c for c in df_preview.columns}
        url_col  = cols_lower.get("url")
        desc_col = cols_lower.get("description")

        if not url_col or not desc_col:
            st.error(f"Could not find `url` and `description` columns. Found: {list(df_preview.columns)}")
            df_preview = None
        else:
            st.success(f"✓  {len(df_preview):,} rows detected · columns: {list(df_preview.columns)}")
            with st.expander("Preview first 5 rows"):
                st.dataframe(df_preview.head(), use_container_width=True)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")

# ── Step 3: Run ────────────────────────────────────────────────────────────────
can_run = bool(df_preview is not None and language)

if st.button("▶  Run Translation", disabled=not can_run):
    client = OpenAI(api_key=OPENAI_API_KEY)
    total = len(df_preview)

    results_data = []
    errors = []

    st.markdown("---")
    st.markdown("**Translation in progress…**")
    progress_bar = st.progress(0)
    status_text  = st.empty()
    metrics_cols = st.columns(3)
    done_count   = metrics_cols[0].empty()
    err_count    = metrics_cols[1].empty()
    eta_display  = metrics_cols[2].empty()

    start_time = time.time()

    for i, row in df_preview.iterrows():
        idx = list(df_preview.index).index(i)
        pct = idx / total

        desc = str(row[desc_col]) if pd.notna(row[desc_col]) else ""
        url  = str(row[url_col])  if pd.notna(row[url_col])  else ""

        status_text.markdown(
            f"<span style='font-size:0.8rem;color:#888580;font-family:JetBrains Mono,monospace;'>"
            f"Row {idx+1} / {total} — {url[:70]}</span>",
            unsafe_allow_html=True,
        )

        if desc.strip():
            translation, error = translate_text(client, desc, language, system_prompt, model_choice)
        else:
            translation, error = "", None

        if error:
            errors.append({"row": idx + 1, "url": url, "error": error})
            translation = ""

        row_result = row.to_dict()
        col_name = f"description_{language.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
        row_result[col_name] = translation
        row_result["translation_status"] = "error" if error else "done"
        results_data.append(row_result)

        elapsed   = time.time() - start_time
        rows_done = idx + 1
        avg       = elapsed / rows_done
        remaining = int(avg * (total - rows_done))
        mins, secs = divmod(remaining, 60)

        progress_bar.progress(min(pct + 1 / total, 1.0))
        done_count.metric("Translated", rows_done)
        err_count.metric("Errors", len(errors))
        eta_display.metric("ETA", f"{mins}m {secs}s" if remaining > 0 else "Done")

    st.session_state.results = pd.DataFrame(results_data)
    st.session_state.errors  = errors
    st.session_state.done    = True
    status_text.markdown(
        "<span style='color:#2e7d52;font-weight:500;'>✓ Translation complete</span>",
        unsafe_allow_html=True,
    )

# ── Step 4: Download ───────────────────────────────────────────────────────────
if st.session_state.done and st.session_state.results is not None:
    st.markdown("---")
    st.markdown('<p class="pc-section">Results</p>', unsafe_allow_html=True)

    res     = st.session_state.results
    done_n  = (res["translation_status"] == "done").sum()
    error_n = (res["translation_status"] == "error").sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total rows", len(res))
    c2.metric("Translated", int(done_n))
    c3.metric("Errors", int(error_n))

    if st.session_state.errors:
        with st.expander(f"⚠️  {error_n} rows had errors — click to review"):
            st.dataframe(pd.DataFrame(st.session_state.errors), use_container_width=True)

    # ── UTF-8 with BOM so Excel opens accented characters correctly ──
    csv_out = res.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇  Download translated CSV",
        data=csv_out,
        file_name=f"translated_{language.lower().replace(' ', '_')}.csv",
        mime="text/csv; charset=utf-8",
    )

    if error_n > 0:
        errors_only = res[res["translation_status"] == "error"]
        st.download_button(
            label="⬇  Download errors only (for re-run)",
            data=errors_only.to_csv(index=False).encode("utf-8-sig"),
            file_name="translation_errors.csv",
            mime="text/csv; charset=utf-8",
        )

    st.markdown("---")
    if st.button("↺  Start a new run"):
        st.session_state.results = None
        st.session_state.errors  = []
        st.session_state.done    = False
        st.rerun()
