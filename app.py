
import math
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Simulador Capacitores",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main > div {
        padding-top: 1.2rem;
    }
    .soft-note {
        color: #444;
        font-size: 0.98rem;
        line-height: 1.5;
    }
    .small-note {
        color: #555;
        font-size: 0.9rem;
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
    </style>
    """,
    unsafe_allow_html=True,
)

SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def superscript_int(n: int) -> str:
    return str(n).translate(SUPERSCRIPT)


def fmt_pt(x: float, decimals: int = 2) -> str:
    s = f"{x:.{decimals}f}"
    return s.replace('.', ',')


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


def svg_resistor(x0, y, length=150, height=24, color="#222"):
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
    pts = " ".join([f"{x},{y_}" for x, y_ in points])
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round" />'


def svg_cap_series(cx, y, plate_h=52, gap=16, color="#222"):
    left = cx - gap / 2
    right = cx + gap / 2
    return f"""
    <line x1=\"{left}\" y1=\"{y - plate_h/2}\" x2=\"{left}\" y2=\"{y + plate_h/2}\" stroke=\"{color}\" stroke-width=\"4\" />
    <line x1=\"{right}\" y1=\"{y - plate_h/2}\" x2=\"{right}\" y2=\"{y + plate_h/2}\" stroke=\"{color}\" stroke-width=\"4\" />
    """


def svg_cap_horizontal(x_left, y, plate_h=54, gap=16, color="#222"):
    x1 = x_left + 34
    x2 = x1 + gap
    return f"""
    <line x1=\"{x_left}\" y1=\"{y}\" x2=\"{x1}\" y2=\"{y}\" stroke=\"{color}\" stroke-width=\"4\" />
    <line x1=\"{x1}\" y1=\"{y - plate_h/2}\" x2=\"{x1}\" y2=\"{y + plate_h/2}\" stroke=\"{color}\" stroke-width=\"4\" />
    <line x1=\"{x2}\" y1=\"{y - plate_h/2}\" x2=\"{x2}\" y2=\"{y + plate_h/2}\" stroke=\"{color}\" stroke-width=\"4\" />
    <line x1=\"{x2}\" y1=\"{y}\" x2=\"{x2 + 34}\" y2=\"{y}\" stroke=\"{color}\" stroke-width=\"4\" />
    """


def circuit_svg(config: str, c1_uF: float, c2_uF: float, r_ohm: float, v_source: float, ceq_uF: float) -> str:
    wire = "#1f2937"
    accent = "#0f766e"
    text = "#111827"
    bg = "#ffffff"

    svg = [
        f'<svg width="1100" height="430" viewBox="0 0 1100 430" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="0" y="0" width="1100" height="430" fill="{bg}" rx="16" />',
        '<style>.label{font: 600 22px Arial, sans-serif; fill:' + text + ';} .small{font: 500 18px Arial, sans-serif; fill:' + text + ';} .tiny{font: 500 16px Arial, sans-serif; fill:' + text + ';}</style>'
    ]

    svg.append('<rect x="70" y="115" width="170" height="200" rx="18" fill="#f8fafc" stroke="#334155" stroke-width="3"/>')
    svg.append('<rect x="96" y="142" width="118" height="54" rx="10" fill="#e2e8f0" stroke="#64748b" stroke-width="2"/>')
    svg.append(f'<text x="155" y="177" text-anchor="middle" class="label">{format_number(v_source)} V</text>')
    svg.append('<text x="155" y="232" text-anchor="middle" class="small">Fonte DC</text>')
    svg.append('<text x="155" y="260" text-anchor="middle" class="tiny">Vf</text>')

    svg.append(f'<line x1="240" y1="165" x2="310" y2="165" stroke="{wire}" stroke-width="4" />')
    svg.append(f'<line x1="240" y1="275" x2="120" y2="275" stroke="{wire}" stroke-width="4" />')
    svg.append(f'<line x1="120" y1="275" x2="120" y2="345" stroke="{wire}" stroke-width="4" />')

    svg.append(f'<line x1="310" y1="165" x2="360" y2="165" stroke="{wire}" stroke-width="4" />')
    svg.append(svg_resistor(360, 165, length=150, height=20, color=wire))
    svg.append(f'<line x1="510" y1="165" x2="560" y2="165" stroke="{wire}" stroke-width="4" />')
    svg.append(f'<text x="435" y="125" text-anchor="middle" class="label">R = {eng_value(r_ohm, "Ω")}</text>')

    svg.append('<rect x="825" y="30" width="220" height="92" rx="14" fill="#f0fdf4" stroke="#16a34a" stroke-width="2.5"/>')
    svg.append('<text x="935" y="66" text-anchor="middle" class="small">Capacitância equivalente</text>')
    svg.append(f'<text x="935" y="98" text-anchor="middle" class="label">Ceq = {eng_value(ceq_uF * 1e-6, "F")}</text>')

    if config == "Série":
        svg.append(f'<line x1="560" y1="165" x2="650" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(svg_cap_series(690, 165, color=accent))
        svg.append(f'<line x1="650" y1="165" x2="682" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="698" y1="165" x2="770" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(svg_cap_series(810, 165, color=accent))
        svg.append(f'<line x1="770" y1="165" x2="802" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="818" y1="165" x2="940" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="940" y1="165" x2="940" y2="345" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="940" y1="345" x2="120" y2="345" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<text x="690" y="120" text-anchor="middle" class="label">C₁ = {format_number(c1_uF)} µF</text>')
        svg.append(f'<text x="810" y="120" text-anchor="middle" class="label">C₂ = {format_number(c2_uF)} µF</text>')
        svg.append('<text x="748" y="225" text-anchor="middle" class="small">Capacitores em série</text>')
    else:
        svg.append(f'<line x1="560" y1="165" x2="640" y2="165" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<circle cx="640" cy="165" r="5" fill="{wire}" />')
        svg.append(f'<line x1="640" y1="165" x2="640" y2="95" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="640" y1="165" x2="640" y2="255" stroke="{wire}" stroke-width="4" />')
        svg.append(svg_cap_horizontal(640, 95, color=accent))
        svg.append(f'<line x1="724" y1="95" x2="850" y2="95" stroke="{wire}" stroke-width="4" />')
        svg.append(svg_cap_horizontal(640, 255, color=accent))
        svg.append(f'<line x1="724" y1="255" x2="850" y2="255" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="850" y1="95" x2="850" y2="255" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<circle cx="850" cy="95" r="5" fill="{wire}" />')
        svg.append(f'<circle cx="850" cy="255" r="5" fill="{wire}" />')
        svg.append(f'<line x1="850" y1="175" x2="940" y2="175" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="940" y1="175" x2="940" y2="345" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<line x1="940" y1="345" x2="120" y2="345" stroke="{wire}" stroke-width="4" />')
        svg.append(f'<text x="760" y="52" text-anchor="middle" class="label">C₁ = {format_number(c1_uF)} µF</text>')
        svg.append(f'<text x="760" y="212" text-anchor="middle" class="label">C₂ = {format_number(c2_uF)} µF</text>')
        svg.append('<text x="770" y="307" text-anchor="middle" class="small">Capacitores em paralelo</text>')

    svg.append('</svg>')
    return "".join(svg)


C_MIN_UF = 50
C_MAX_UF = 500
R_MIN_OHM = 100
R_MAX_OHM = 5000
V_MIN = 1
V_MAX = 24

TAU_MAX_GLOBAL = R_MAX_OHM * ((C_MAX_UF + C_MAX_UF) * 1e-6)
T_MAX_GLOBAL = 5 * TAU_MAX_GLOBAL
Ceq_MAX_GLOBAL = (C_MAX_UF + C_MAX_UF) * 1e-6
I_MAX_GLOBAL = V_MAX / R_MIN_OHM
Q_MAX_GLOBAL = Ceq_MAX_GLOBAL * V_MAX

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
        config = st.radio("Associação dos capacitores", ["Série", "Paralelo"], horizontal=True)
        r_ohm = st.slider("Resistência R (Ω)", R_MIN_OHM, R_MAX_OHM, 1000, step=100)
    with p3:
        v_source = st.slider("Tensão da fonte V (V)", V_MIN, V_MAX, 12, step=1)
        st.markdown(f"**Faixas fixas dos gráficos:** 0 a {format_number(T_MAX_GLOBAL)} s no eixo do tempo.")

C1 = c1_uF * 1e-6
C2 = c2_uF * 1e-6
if config == "Série":
    Ceq = (C1 * C2) / (C1 + C2)
else:
    Ceq = C1 + C2

tau = r_ohm * Ceq if r_ohm * Ceq > 0 else 1e-12
V0 = v_source
I0 = v_source / r_ohm

t = np.linspace(0, T_MAX_GLOBAL, 1200)
Vc = V0 * (1 - np.exp(-t / tau))
I = I0 * np.exp(-t / tau)
q = Ceq * Vc

vc_tau = V0 * (1 - math.exp(-1))
i_tau = I0 * math.exp(-1)
q_tau = Ceq * vc_tau

with st.container(border=True):
    st.subheader("Imagem do circuito RC")
    st.markdown(
        "<p class='small-note'>Em telas pequenas, deslize horizontalmente a figura com o dedo para visualizar o circuito completo.</p>",
        unsafe_allow_html=True,
    )
    svg = circuit_svg(config, c1_uF, c2_uF, r_ohm, v_source, Ceq * 1e6)
    st.markdown(f'<div class="circuit-scroll">{svg}</div>', unsafe_allow_html=True)

with st.container(border=True):
    st.subheader("Capacitância equivalente Ceq")
    st.latex(r"\text{Série:}\quad C_{eq} = \frac{C_1 C_2}{C_1 + C_2}")
    st.latex(r"\text{Paralelo:}\quad C_{eq} = C_1 + C_2")
    if config == "Série":
        st.latex(rf"C_{{eq}} = \frac{{{c1_uF:.2f}\,\mu F \cdot {c2_uF:.2f}\,\mu F}}{{{c1_uF:.2f}\,\mu F + {c2_uF:.2f}\,\mu F}} = {Ceq*1e6:.3f}\,\mu F")
    else:
        st.latex(rf"C_{{eq}} = {c1_uF:.2f}\,\mu F + {c2_uF:.2f}\,\mu F = {Ceq*1e6:.3f}\,\mu F")
    st.success(f"Valor de Ceq: {eng_value(Ceq, 'F')}")

with st.container(border=True):
    st.subheader("Tempo de relaxação tau")
    st.latex(r"\tau = R\,C_{eq}")
    st.latex(rf"\tau = {r_ohm:.0f}\,\Omega \cdot {latex_num(Ceq, 6)}\,F = {latex_num(tau, 6)}\,s")
    st.success(f"Valor de tau: {eng_value(tau, 's')}")

with st.container(border=True):
    st.subheader("Tensão máxima V0")
    st.write(f"Quando totalmente carregado, o capacitor terá tensão máxima igual à tensão da fonte: **{eng_value(v_source, 'V')}**.")

with st.container(border=True):
    st.subheader("Corrente máxima I0")
    st.write("**Balanço de tensão elétrica:**")
    st.latex(r"V_f = V_r + V_c")
    st.write("onde **Vf**, **Vr** e **Vc** são as tensões na fonte, no resistor e no capacitor, respectivamente.")
    st.write("Quando totalmente descarregado, não há tensão no capacitor. Nessa situação, a tensão do resistor equivale à tensão da fonte. Logo, pela Lei de Ohm, é possível determinar a corrente máxima:")
    st.latex(r"V_r = R\,I_0 \Rightarrow I_0 = \frac{V_f}{R}")
    st.latex(rf"I_0 = \frac{{{v_source:.2f}\,V}}{{{r_ohm:.0f}\,\Omega}} = {latex_num(I0, 6)}\,A")
    st.success(f"Valor da corrente máxima: {eng_value(I0, 'A')}")

with st.container(border=True):
    st.subheader("Comportamento durante carga do capacitor equivalente")
    st.write("Equações em função do tempo para o capacitor equivalente em um circuito RC em carga:")
    st.latex(r"V_c(t) = V_0\left(1 - e^{-t/\tau}\right)")
    st.latex(r"I(t) = I_0 e^{-t/\tau}")
    st.latex(r"q(t) = C_{eq}\,V_c(t) = C_{eq}\,V_0\left(1 - e^{-t/\tau}\right)")
    st.markdown("**Equações com os valores substituídos:**")
    st.latex(rf"V_c(t) = {v_source:.2f}\left(1 - e^{{-t/{latex_num(tau, 6)}}}\right)\,V")
    st.latex(rf"I(t) = {latex_num(I0, 6)}\,e^{{-t/{latex_num(tau, 6)}}}\,A")
    st.latex(rf"q(t) = {latex_num(Ceq, 6)}\cdot {v_source:.2f}\left(1 - e^{{-t/{latex_num(tau, 6)}}}\right)\,C")
    st.info(f"No instante t = tau = {eng_value(tau, 's')}, a tensão no capacitor atinge aproximadamente 63,2% de V0, enquanto a corrente cai para aproximadamente 36,8% de I0.")


def make_plot(x, y, title, y_title, y_range, tau_x, tau_y, curve_name, line_color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=curve_name, line=dict(color=line_color, width=3), hovertemplate="t = %{x:.3f} s<br>" + y_title + " = %{y:.6f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[tau_x], y=[tau_y], mode="markers", name="τ", marker=dict(size=10, color="#111827", symbol="circle"), hovertemplate="τ = %{x:.4f} s<br>Valor = %{y:.6f}<extra></extra>"))
    fig.add_vline(x=tau_x, line_width=2, line_dash="dash", line_color="#6b7280")
    fig.add_hline(y=tau_y, line_width=2, line_dash="dot", line_color="#9ca3af")
    fig.add_annotation(x=tau_x, y=tau_y, text=f"τ = {tau_x:.4f} s<br>y = {tau_y:.6f}", showarrow=True, arrowhead=2, ax=60, ay=-60, bgcolor="rgba(255,255,255,0.85)", bordercolor="#d1d5db")
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=55, b=20), height=420, xaxis=dict(title="Tempo t (s)", range=[0, T_MAX_GLOBAL], fixedrange=True), yaxis=dict(title=y_title, range=y_range, fixedrange=True), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
    return fig

with st.container(border=True):
    st.subheader("Gráficos durante carga do capacitor equivalente")
    st.write("Equações mostradas nos gráficos:")
    st.latex(r"V_c(t) = V_0\left(1 - e^{-t/\tau}\right)")
    st.latex(r"I(t) = I_0 e^{-t/\tau}")
    st.latex(r"q(t) = C_{eq}\,V_0\left(1 - e^{-t/\tau}\right)")
    st.markdown(f"<p class='small-note'>Os eixos permanecem fixos para facilitar a comparação visual ao alterar os sliders. Tempo: 0 a {format_number(T_MAX_GLOBAL)} s.</p>", unsafe_allow_html=True)
    fig_v = make_plot(t, Vc, "Tensão no capacitor equivalente Vc(t)", "Vc(t) [V]", [0, V_MAX * 1.05], tau, vc_tau, "Vc(t)", "#2563eb")
    fig_i = make_plot(t, I, "Corrente no circuito I(t)", "I(t) [A]", [0, I_MAX_GLOBAL * 1.05], tau, i_tau, "I(t)", "#dc2626")
    fig_q = make_plot(t, q, "Carga armazenada q(t)", "q(t) [C]", [0, Q_MAX_GLOBAL * 1.05], tau, q_tau, "q(t)", "#16a34a")
    st.plotly_chart(fig_v, use_container_width=True, config={"displaylogo": False, "responsive": True})
    st.plotly_chart(fig_i, use_container_width=True, config={"displaylogo": False, "responsive": True})
    st.plotly_chart(fig_q, use_container_width=True, config={"displaylogo": False, "responsive": True})

with st.expander("Observações didáticas"):
    st.markdown(
        """
        - O simulador considera **capacitores ideais** e **fonte contínua ideal**.
        - O comportamento temporal é calculado a partir do **capacitor equivalente** do conjunto selecionado.
        - Em associação em **série**, a corrente é a mesma em ambos os capacitores; em **paralelo**, a tensão é a mesma em ambos.
        - Para publicação em Streamlit Cloud ou GitHub, mantenha **app.py**, **requirements.txt** e **logo_maua.png** na raiz do repositório.
        """
    )
