import math
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# Configuração da página
# =========================================================
st.set_page_config(
    page_title="Simulador Capacitores",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# Estilos
# =========================================================
st.markdown(
    """
    <style>
    .main > div {
        padding-top: 1.1rem;
    }
    .soft-note {
        color: #444;
        font-size: 0.98rem;
        line-height: 1.5;
    }
    .small-note {
        color: #555;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .circuit-scroll {
        width: 100%;
        overflow-x: auto;
        overflow-y: hidden;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        background: white;
        padding: 0.4rem;
        -webkit-overflow-scrolling: touch;
        touch-action: pan-x pan-y;
    }
    .header-title {
        margin-bottom: 0.2rem;
    }
    .logo-fallback {
        border: 1px dashed #b6beca;
        border-radius: 16px;
        padding: 1rem;
        text-align: center;
        color: #5b6470;
        background: #fafbfd;
    }
    .section-title {
        font-size: 1.35rem;
        font-weight: 600;
        margin-bottom: 0.35rem;
        color: #111827;
    }
    .result-line {
        font-size: 1rem;
        color: #111827;
        margin-top: 0.25rem;
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Funções auxiliares
# =========================================================
SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def superscript_int(n: int) -> str:
    return str(n).translate(SUPERSCRIPT)


def fmt_pt(x: float, decimals: int = 2) -> str:
    s = f"{x:.{decimals}f}"
    return s.replace(".", ",")


def sci_unicode(x: float, decimals: int = 2) -> str:
    if x == 0:
        return "0"
    exp = int(math.floor(math.log10(abs(x))))
    mant = x / (10 ** exp)
    return f"{fmt_pt(mant, decimals)} × 10{superscript_int(exp)}"


def format_number(x: float, decimals: int = 2) -> str:
    ax = abs(x)
    if x == 0:
        return "0"
    if 1e-2 <= ax < 1e4:
        return fmt_pt(x, decimals)
    return sci_unicode(x, decimals)


def eng_value(value: float, base_unit: str) -> str:
    av = abs(value)

    if base_unit == "F":
        if av >= 1:
            return f"{format_number(value)} F"
        if av >= 1e-3:
            return f"{format_number(value * 1e3)} mF"
        if av >= 1e-6:
            return f"{format_number(value * 1e6)} µF"
        if av >= 1e-9:
            return f"{format_number(value * 1e9)} nF"
        return f"{format_number(value)} F"

    if base_unit == "A":
        if av >= 1:
            return f"{format_number(value)} A"
        if av >= 1e-3:
            return f"{format_number(value * 1e3)} mA"
        if av >= 1e-6:
            return f"{format_number(value * 1e6)} µA"
        return f"{format_number(value)} A"

    if base_unit == "C":
        if av >= 1:
            return f"{format_number(value)} C"
        if av >= 1e-3:
            return f"{format_number(value * 1e3)} mC"
        if av >= 1e-6:
            return f"{format_number(value * 1e6)} µC"
        return f"{format_number(value)} C"

    if base_unit == "s":
        if av >= 1:
            return f"{format_number(value)} s"
        if av >= 1e-3:
            return f"{format_number(value * 1e3)} ms"
        if av >= 1e-6:
            return f"{format_number(value * 1e6)} µs"
        return f"{format_number(value)} s"

    if base_unit == "Ω":
        if av >= 1e6:
            return f"{format_number(value / 1e6)} MΩ"
        if av >= 1e3:
            return f"{format_number(value / 1e3)} kΩ"
        return f"{format_number(value)} Ω"

    if base_unit == "V":
        return f"{format_number(value)} V"

    return f"{format_number(value)} {base_unit}"


def latex_num(x: float, decimals: int = 3) -> str:
    if x == 0:
        return "0"
    ax = abs(x)
    if 1e-2 <= ax < 1e4:
        return f"{x:.{decimals}f}"
    exp = int(math.floor(math.log10(ax)))
    mant = x / (10 ** exp)
    return f"{mant:.{decimals}f}\\times 10^{{{exp}}}"


# =========================================================
# Desenho do circuito em SVG
# =========================================================
def svg_resistor(x0, y, length=150, height=22, color="#222"):
    step = length / 8
    points = [
        (x0, y),
        (x0 + step, y - height),
        (x0 + 2 * step, y + height),
        (x0 + 3 * step, y - height),
        (x0 + 4 * step, y + height),
        (x0 + 5 * step, y - height),
        (x0 + 6 * step, y + height),
        (x0 + 7 * step, y - height),
        (x0 + 8 * step, y),
    ]
    pts = " ".join([f"{x},{yy}" for x, yy in points])
    return (
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="4" '
        f'stroke-linejoin="round" stroke-linecap="round" />'
    )


def svg_cap_series(cx, y, plate_h=54, gap=16, color="#222"):
    left = cx - gap / 2
    right = cx + gap / 2
    return f"""
    <line x1="{left}" y1="{y - plate_h/2}" x2="{left}" y2="{y + plate_h/2}" stroke="{color}" stroke-width="4" />
    <line x1="{right}" y1="{y - plate_h/2}" x2="{right}" y2="{y + plate_h/2}" stroke="{color}" stroke-width="4" />
    """


def svg_cap_horizontal(x_left, y, plate_h=54, gap=16, color="#222"):
    x1 = x_left + 34
    x2 = x1 + gap
    return f"""
    <line x1="{x_left}" y1="{y}" x2="{x1}" y2="{y}" stroke="{color}" stroke-width="4" />
    <line x1="{x1}" y1="{y - plate_h/2}" x2="{x1}" y2="{y + plate_h/2}" stroke="{color}" stroke-width="4" />
    <line x1="{x2}" y1="{y - plate_h/2}" x2="{x2}" y2="{y + plate_h/2}" stroke="{color}" stroke-width="4" />
    <line x1="{x2}" y1="{y}" x2="{x2 + 34}" y2="{y}" stroke="{color}" stroke-width="4" />
    """


def ceq_svg_label() -> str:
    return """
    C<tspan baseline-shift="sub" font-size="70%">eq</tspan>
    """


def circuit_svg(config: str, c1_uF: float, c2_uF: float, r_ohm: float, v_source: float, ceq_uF: float) -> str:
    wire = "#1f2937"
    accent = "#0f766e"
    text = "#111827"
    bg = "#ffffff"

    width = 1320
    height = 430

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{bg}" rx="16" />',
        '<style>'
        '.label{font: 600 22px Arial, sans-serif; fill:' + text + ';}'
        '.small{font: 500 18px Arial, sans-serif; fill:' + text + ';}'
        '.tiny{font: 500 16px Arial, sans-serif; fill:' + text + ';}'
        '</style>'
    ]

    # Fonte
    svg.append('<rect x="70" y="115" width="170" height="200" rx="18" fill="#f8fafc" stroke="#334155" stroke-width="3"/>')
    svg.append('<rect x="96" y="142" width="118" height="54" rx="10" fill="#e2e8f0" stroke="#64748b" stroke-width="2"/>')
    svg.append(f'<text x="155" y="177" text-anchor="middle" class="label">{format_number(v_source)} V</text>')
    svg.append('<text x="155" y="232" text-anchor="middle" class="small">Fonte DC</text>')
    svg.append('<text x="155" y="260" text-anchor="middle" class="tiny">Vf</text>')

    # Caminho até resistor
    svg.append(f'<line x1="120" y1="275" x2="120" y2="375" stroke="{wire}" stroke-width="4" />')
    svg.append(f'<line x1="240" y1="165" x2="310" y2="165" stroke="{wire}" stroke-width="4" />')
    svg.append(f'<line x1="310" y1="165" x2="360" y2="165" stroke="{wire}" stroke-width="4" />')
    svg.append(svg_resistor(360, 165, length=150, height=20, color=wire))
    svg.append(f'<line x1="510" y1="165" x2="560" y2="165" stroke="{wire}" stroke-width="4" />')
    svg.append(f'<text x="435" y="125" text-anchor="middle" class="label">R = {eng_value(r_ohm, "Ω")}</text>')

    # Box de C_eq
    svg.append('<rect x="1080" y="28" width="210" height="92" rx="14" fill="#f0fdf4" stroke="#16a34a" stroke-width="2.5"/>')
    svg.append('<text x="1185" y="63" text-anchor="middle" class="small">Capacitância equivalente</text>')
    svg.append(
        f'<text x="1185" y="95" text-anchor="middle" class="label">C<tspan baseline-shift="sub" font-size="70%">eq</tspan> = {eng_value(ceq_uF * 1e-6, "F")}</text>'
    )

    if config == "Série":
        # Série
        svg.append(f'<line x1="560" y1="165" x2="660" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(svg_cap_series(700, 165, color=accent))
        svg.append(f'<line x1="660" y1="165" x2="692" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="708" y1="165" x2="810" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(svg_cap_series(850, 165, color=accent))
        svg.append(f'<line x1="810" y1="165" x2="842" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="858" y1="165" x2="1000" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="1000" y1="165" x2="1000" y2="345" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="1000" y1="345" x2="120" y2="345" stroke="{wire}" stroke-width="4" />')


        # fio vertical final reduzido
        svg.append(f'<line x1="1000" y1="165" x2="1000" y2="255" stroke="{wire}" stroke-width="4" />')

        # sem fio horizontal final de retorno
        svg.append(f'<text x="850" y="120" text-anchor="middle" class="label">C₂ = {format_number(c2_uF)} µF</text>')
        svg.append('<text x="775" y="225" text-anchor="middle" class="small">Capacitores em série</text>')
        svg.append(f'<text x="700" y="265" text-anchor="middle" class="label">C₁ = {format_number(c1_uF)} µF</text>')

    else:
        # Paralelo
        
        svg.append(f'<line x1="560" y1="165" x2="650" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<circle cx="650" cy="165" r="5" fill="{wire}" />')
        svg.append(f'<line x1="650" y1="165" x2="650" y2="95" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="650" y1="165" x2="650" y2="255" stroke="{wire}" stroke-width="4" />')

        svg.append(svg_cap_horizontal(650, 95, color=accent))
        svg.append(f'<line x1="734" y1="95" x2="900" y2="95" stroke="{wire}" stroke-width="4" />')

        svg.append(svg_cap_horizontal(650, 255, color=accent))
        svg.append(f'<line x1="734" y1="255" x2="900" y2="255" stroke="{wire}" stroke-width="4" />')

        svg.append(f'<line x1="900" y1="95" x2="900" y2="255" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<circle cx="900" cy="95" r="5" fill="{wire}" />')
        svg.append(f'<circle cx="900" cy="255" r="5" fill="{wire}" />')
        svg.append(f'<line x1="900" y1="175" x2="1000" y2="175" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="1000" y1="175" x2="1000" y2="345" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="1000" y1="345" x2="120" y2="345" stroke="{wire}" stroke-width="4" />')

        svg.append(f'<text x="790" y="52" text-anchor="middle" class="label">C₁ = {format_number(c1_uF)} µF</text>')
        svg.append(f'<text x="790" y="212" text-anchor="middle" class="label">C₂ = {format_number(c2_uF)} µF</text>')
        svg.append('<text x="800" y="307" text-anchor="middle" class="small">Capacitores em paralelo</text>')

    svg.append("</svg>")
    return "".join(svg)


# =========================================================
# Faixas dos sliders
# =========================================================
C_MIN_UF = 50
C_MAX_UF = 500
R_MIN_OHM = 100
R_MAX_OHM = 5000
V_MIN = 1
V_MAX = 24


# =========================================================
# Cabeçalho
# =========================================================
col_logo, col_texto = st.columns([1.05, 3.0], gap="large")

with col_logo:
    logo_path = Path("logo_maua.png")
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.markdown(
            """
            <div class="logo-fallback">
                <strong>logo_maua.png</strong><br/>
                Coloque este arquivo na raiz do projeto para exibir a logo.
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_texto:
    st.markdown("<h1 class='header-title'>Simulador Capacitores</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='soft-note'>Estude o comportamento de circuito RC com capacitores ideais sendo carregados.</p>",
        unsafe_allow_html=True,
    )


# =========================================================
# Parâmetros
# =========================================================
with st.container(border=True):
    st.subheader("Parâmetros")
    st.markdown(
        "<p class='small-note'>Use os controles abaixo para comparar a associação em série e em paralelo.</p>",
        unsafe_allow_html=True,
    )

    p1, p2, p3 = st.columns(3, gap="large")

    with p1:
        c1_uF = st.slider("Capacitância C₁ (µF)", C_MIN_UF, C_MAX_UF, 220, step=10)
        c2_uF = st.slider("Capacitância C₂ (µF)", C_MIN_UF, C_MAX_UF, 220, step=10)

    with p2:
        config = st.radio(
            "Associação dos capacitores",
            ["Série", "Paralelo"],
            horizontal=True,
        )
        r_ohm = st.slider("Resistência R (Ω)", R_MIN_OHM, R_MAX_OHM, 1000, step=100)

    with p3:
        v_source = st.slider("Tensão da fonte V (V)", V_MIN, V_MAX, 12, step=1)


# =========================================================
# Grandezas derivadas
# =========================================================
C1 = c1_uF * 1e-6
C2 = c2_uF * 1e-6

if config == "Série":
    Ceq = (C1 * C2) / (C1 + C2)
else:
    Ceq = C1 + C2

tau = r_ohm * Ceq
tau = max(tau, 1e-12)

V0 = v_source
I0 = v_source / r_ohm
q0 = Ceq * V0

# Tempo dinâmico
t_end = 5 * tau
t_end = max(t_end, 1e-9)

t = np.linspace(0, t_end, 1200)

Vc = V0 * (1 - np.exp(-t / tau))
I = I0 * np.exp(-t / tau)
q = q0 * (1 - np.exp(-t / tau))

V_tau = V0 * (1 - math.exp(-1))
I_tau = I0 * math.exp(-1)
q_tau = q0 * (1 - math.exp(-1))


# =========================================================
# Imagem do circuito RC
# =========================================================
with st.container(border=True):
    st.subheader("Imagem do circuito RC")
    st.markdown(
        "<p class='small-note'>Em telas pequenas, deslize horizontalmente a figura com o dedo para visualizar o circuito completo.</p>",
        unsafe_allow_html=True,
    )
    svg = circuit_svg(config, c1_uF, c2_uF, r_ohm, v_source, Ceq * 1e6)
    st.markdown(f'<div class="circuit-scroll">{svg}</div>', unsafe_allow_html=True)


# =========================================================
# Capacitância equivalente
# =========================================================
with st.container(border=True):
    st.markdown("<div class='section-title'>Capacitância equivalente C<sub>eq</sub></div>", unsafe_allow_html=True)

    # Série em uma linha só
    st.latex(
        r"\text{Série:}\quad \frac{1}{C_{eq}} = \frac{1}{C_1} + \frac{1}{C_2} \qquad C_{eq} = \frac{C_1 C_2}{C_1 + C_2}"
    )
    st.latex(r"\text{Paralelo:}\quad C_{eq} = C_1 + C_2")

    if config == "Série":
        st.latex(
            rf"\frac{{1}}{{C_{{eq}}}} = \frac{{1}}{{{c1_uF:.2f}\,\mu F}} + \frac{{1}}{{{c2_uF:.2f}\,\mu F}}"
        )
        st.latex(
            rf"C_{{eq}} = \frac{{{c1_uF:.2f}\,\mu F \cdot {c2_uF:.2f}\,\mu F}}{{{c1_uF:.2f}\,\mu F + {c2_uF:.2f}\,\mu F}} = {Ceq*1e6:.3f}\,\mu F"
        )
    else:
        st.latex(
            rf"C_{{eq}} = {c1_uF:.2f}\,\mu F + {c2_uF:.2f}\,\mu F = {Ceq*1e6:.3f}\,\mu F"
        )

    st.markdown(
        f"<div class='result-line'><strong>Valor de C<sub>eq</sub>:</strong> {eng_value(Ceq, 'F')}</div>",
        unsafe_allow_html=True,
    )


# =========================================================
# Tempo de relaxação τ
# =========================================================
with st.container(border=True):
    st.subheader("Tempo de relaxação τ")
    st.latex(r"\tau = R\,C_{eq}")
    st.latex(
        rf"\tau = {r_ohm:.0f}\,\Omega \cdot {latex_num(Ceq, 6)}\,F = {latex_num(tau, 6)}\,s"
    )
    st.success(f"Valor de τ: {eng_value(tau, 's')}")

    st.info(
        f"No instante t = tau = {eng_value(tau, 's')}, a tensão no capacitor atinge aproximadamente "
        f"63,2% de V0, enquanto a corrente cai para aproximadamente 36,8% de I0."
    )


# =========================================================
# Tensão máxima V0
# =========================================================
with st.container(border=True):
    st.subheader("Tensão máxima V0")
    st.write(
        f"Quando totalmente carregado, o capacitor terá tensão máxima igual à tensão da fonte: **{eng_value(v_source, 'V')}**."
    )


# =========================================================
# Corrente máxima I0
# =========================================================
with st.container(border=True):
    st.subheader("Corrente máxima I0")
    st.write("**Balanço de tensão elétrica:**")
    st.latex(r"V_f = V_r + V_c")
    st.write("onde **Vf**, **Vr** e **Vc** são as tensões na fonte, no resistor e no capacitor, respectivamente.")
    st.write(
        "Quando totalmente descarregado, não há tensão no capacitor. Nessa situação, a tensão do resistor equivale à tensão da fonte. "
        "Logo, pela Lei de Ohm, é possível determinar a corrente máxima:"
    )
    st.latex(r"V_r = R\,I_0 \Rightarrow I_0 = \frac{V_f}{R}")
    st.latex(
        rf"I_0 = \frac{{{v_source:.2f}\,V}}{{{r_ohm:.0f}\,\Omega}} = {latex_num(I0, 6)}\,A"
    )
    st.success(f"Valor da corrente máxima: {eng_value(I0, 'A')}")


# =========================================================
# Comportamento durante carga do capacitor equivalente
# =========================================================
with st.container(border=True):
    st.markdown(
        "<div class='section-title'>Comportamento durante carga do capacitor equivalente</div>",
        unsafe_allow_html=True,
    )

    st.write("Equações em função do tempo para o capacitor equivalente em um circuito RC em carga:")

    st.latex(r"V_c(t) = V_0\left(1 - e^{-t/\tau}\right)")
    st.latex(r"I(t) = I_0\,e^{-t/\tau}")
    st.latex(r"q(t) = C_{eq}\,V_c(t) = C_{eq}\,V_0\left(1 - e^{-t/\tau}\right)")

    st.markdown("**Equações com os valores substituídos:**")

    st.latex(
        rf"V_c(t) = {v_source:.2f}\left(1 - e^{{-t/{latex_num(tau, 6)}}}\right)\,V"
    )

    st.latex(
        rf"I(t) = {latex_num(I0, 6)}\,e^{{-t/{latex_num(tau, 6)}}}\,A"
    )

    st.latex(
        rf"q(t) = {latex_num(q0, 6)}\left(1 - e^{{-t/{latex_num(tau, 6)}}}\right)\,C"
    )


# =========================================================
# Gráficos
# =========================================================
PLOT_FONT_COLOR = "#111827"
GRID_COLOR = "#d1d5db"
TAU_COLOR = "#111827"
MAX_COLOR = "#7c3aed"


def plot_config():
    return {
        "displaylogo": False,
        "displayModeBar": False,
        "scrollZoom": False,
        "responsive": True,
    }


def base_layout(fig, title, y_title, x_range, y_range):
    fig.update_layout(
        title=dict(text=title, font=dict(size=20, color=PLOT_FONT_COLOR)),
        margin=dict(l=20, r=20, t=60, b=20),
        height=430,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=PLOT_FONT_COLOR, size=14),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(color=PLOT_FONT_COLOR),
        ),
        xaxis=dict(
            title="Tempo t (s)",
            range=x_range,
            fixedrange=True,
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            tickfont=dict(color=PLOT_FONT_COLOR),
            title_font=dict(color=PLOT_FONT_COLOR),
        ),
        yaxis=dict(
            title=y_title,
            range=y_range,
            fixedrange=True,
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            tickfont=dict(color=PLOT_FONT_COLOR),
            title_font=dict(color=PLOT_FONT_COLOR),
        ),
    )
    return fig


def add_tau_marker(fig, tau_x, tau_y, label_text):
    fig.add_trace(
        go.Scatter(
            x=[tau_x],
            y=[tau_y],
            mode="markers",
            name="τ",
            marker=dict(size=10, color=TAU_COLOR, symbol="circle"),
            hovertemplate="τ = %{x:.4f} s<br>Valor = %{y:.6f}<extra></extra>",
            showlegend=True,
        )
    )
    fig.add_vline(x=tau_x, line_width=2, line_dash="dash", line_color="#4b5563")
    fig.add_hline(y=tau_y, line_width=1.8, line_dash="dot", line_color="#6b7280")

    fig.add_annotation(
        x=tau_x,
        y=tau_y,
        text=label_text,
        showarrow=True,
        arrowhead=2,
        ax=70,
        ay=-60,
        font=dict(color=PLOT_FONT_COLOR, size=13),
        bgcolor="rgba(255,255,255,0.96)",
        bordercolor="#9ca3af",
        borderwidth=1.2,
    )


def add_max_indicator(fig, max_value, label_text, x_pos_label, y_pos_label):
    fig.add_hline(y=max_value, line_width=2, line_dash="dash", line_color=MAX_COLOR)

    fig.add_annotation(
        x=x_pos_label,
        y=y_pos_label,
        text=label_text,
        showarrow=False,
        font=dict(color=PLOT_FONT_COLOR, size=13),
        bgcolor="rgba(255,255,255,0.96)",
        bordercolor=MAX_COLOR,
        borderwidth=1.2,
    )


def make_voltage_plot(t, Vc, tau, V_tau, V0, t_end):
    x_margin = 0.10 * t_end
    x_range = [0, t_end + x_margin]
    y_range = [0, V0 * 1.18]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=t,
            y=Vc,
            mode="lines",
            name="Vc(t)",
            line=dict(color="#2563eb", width=4),
            hovertemplate="t = %{x:.4f} s<br>Vc(t) = %{y:.6f} V<extra></extra>",
        )
    )

    add_tau_marker(
        fig,
        tau_x=tau,
        tau_y=V_tau,
        label_text=f"τ = {format_number(tau, 4)} s<br>V(τ) = {format_number(V_tau, 4)} V",
    )

    add_max_indicator(
        fig,
        max_value=V0,
        label_text=f"V₀ = {eng_value(V0, 'V')}",
        x_pos_label=t_end * 0.72,
        y_pos_label=V0 * 1.03,
    )

    base_layout(
        fig,
        title="Tensão no capacitor equivalente Vc(t)",
        y_title="Vc(t) [V]",
        x_range=x_range,
        y_range=y_range,
    )
    return fig


def make_current_plot(t, I, tau, I_tau, I0, t_end):
    x_margin = 0.10 * t_end
    x_range = [0, t_end + x_margin]
    y_range = [0, I0 * 1.22]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=t,
            y=I,
            mode="lines",
            name="I(t)",
            line=dict(color="#dc2626", width=4),
            hovertemplate="t = %{x:.4f} s<br>I(t) = %{y:.6f} A<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[I0],
            mode="markers",
            name="I₀",
            marker=dict(size=10, color=MAX_COLOR, symbol="diamond"),
            hovertemplate="I₀ = %{y:.6f} A<extra></extra>",
            showlegend=True,
        )
    )

    add_tau_marker(
        fig,
        tau_x=tau,
        tau_y=I_tau,
        label_text=f"τ = {format_number(tau, 4)} s<br>I(τ) = {format_number(I_tau, 6)} A",
    )

    add_max_indicator(
        fig,
        max_value=I0,
        label_text=f"I₀ = {eng_value(I0, 'A')}",
        x_pos_label=t_end * 0.22,
        y_pos_label=I0 * 1.07,
    )

    base_layout(
        fig,
        title="Corrente no capacitor equivalente I(t)",
        y_title="I(t) [A]",
        x_range=x_range,
        y_range=y_range,
    )
    return fig


def make_charge_plot(t, q, tau, q_tau, q0, t_end):
    x_margin = 0.10 * t_end
    x_range = [0, t_end + x_margin]
    y_range = [0, q0 * 1.18]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=t,
            y=q,
            mode="lines",
            name="q(t)",
            line=dict(color="#16a34a", width=4),
            hovertemplate="t = %{x:.4f} s<br>q(t) = %{y:.6f} C<extra></extra>",
        )
    )

    add_tau_marker(
        fig,
        tau_x=tau,
        tau_y=q_tau,
        label_text=f"τ = {format_number(tau, 4)} s<br>q(τ) = {format_number(q_tau, 6)} C",
    )

    add_max_indicator(
        fig,
        max_value=q0,
        label_text=f"q₀ = {eng_value(q0, 'C')}",
        x_pos_label=t_end * 0.72,
        y_pos_label=q0 * 1.03,
    )

    base_layout(
        fig,
        title="Carga armazenada q(t)",
        y_title="q(t) [C]",
        x_range=x_range,
        y_range=y_range,
    )
    return fig


# =========================================================
# Gráficos durante carga do capacitor equivalente
# =========================================================
with st.container(border=True):
    st.markdown(
        "<div class='section-title'>Gráficos durante carga do capacitor equivalente</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='small-note'>Os eixos são ajustados automaticamente para cada situação e ficam bloqueados para interação.</p>",
        unsafe_allow_html=True,
    )

    fig_v = make_voltage_plot(t, Vc, tau, V_tau, V0, t_end)
    fig_i = make_current_plot(t, I, tau, I_tau, I0, t_end)
    fig_q = make_charge_plot(t, q, tau, q_tau, q0, t_end)

    st.plotly_chart(fig_v, use_container_width=True, config=plot_config())
    st.plotly_chart(fig_i, use_container_width=True, config=plot_config())
    st.plotly_chart(fig_q, use_container_width=True, config=plot_config())
