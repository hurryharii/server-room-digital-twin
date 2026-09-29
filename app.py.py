import streamlit as st
import pandas as pd
import math

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Data Center Digital Twin",
    page_icon="🖥️",
    layout="wide"
)

# ============================================================
# DARK BLUE THEME
# ============================================================

st.markdown("""
<style>
.stApp {
    background-color: #071A33;
    color: white;
}

[data-testid="stSidebar"] {
    background-color: #63C7FF;
}

h1, h2, h3{
    color: #63C7FF !important;
}

h4{
color:#63C7FF !important;}

p, label, .stMarkdown, .stCaption,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: white !important;
}

.stMetric {
    background-color: #0D2948;
    border: 1px solid #1D5A86;
    padding: 12px;
    border-radius: 10px;
}

.info-box {
    background-color: #0D2948;
    border-left: 4px solid #0D2948;
    padding: 12px;
    border-radius: 6px;
}

.small-text {
    color: #B8C7D9;
    font-size: 0.9rem;
}

hr {
    border-color: #1D5A86;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# CONSTANTS
# ============================================================

IDLE_POWER = 100       # W per server
MAX_POWER = 300        # W per server


# ============================================================
# POWER MODEL
# ============================================================

def calculate_power(servers, workload):

    power_per_server = (
        IDLE_POWER
        + (MAX_POWER - IDLE_POWER) * workload / 100
    )

    total_power = power_per_server * servers

    return power_per_server, total_power


# ============================================================
# THERMAL MODEL
# ============================================================

def calculate_temperature_response(
    heat,
    cooling,
    ambient,
    thermal_resistance,
    thermal_capacitance,
    simulation_time=300,
    dt=5
):

    """
    Simplified lumped thermal model:

    Cth * dT/dt =
        Heat - Cooling - Heat_loss

    Heat_loss =
        (Temperature - Ambient) / Rth

    """

    if thermal_resistance <= 0 or thermal_capacitance <= 0:
        return [0], [ambient]

    temperature = ambient

    times = []
    temperatures = []

    net_heat = heat - cooling

    equilibrium_temperature = (
        ambient
        + net_heat * thermal_resistance
    )

    # Stable first-order response
    response_factor = math.exp(
        -dt /
        (thermal_resistance * thermal_capacitance)
    )

    for second in range(
        0,
        simulation_time + 1,
        dt
    ):

        if second > 0:

            temperature = (
                equilibrium_temperature
                +
                (temperature - equilibrium_temperature)
                * response_factor
            )

        # Temperature should not fall below ambient
        temperature = max(
            temperature,
            ambient
        )

        times.append(second)
        temperatures.append(temperature)

    return times, temperatures


# ============================================================
# TEMPERATURE STATUS
# ============================================================

def temperature_status(temperature):

    if temperature >= 35:
        return "🔴 CRITICAL"

    elif temperature >= 30:
        return "🟠 WARNING"

    elif temperature >= 27:
        return "🟡 CAUTION"

    else:
        return "🟢 NORMAL"


# ============================================================
# SERVER DISTRIBUTION
# ============================================================

def distribute_servers(total_servers, racks):

    """
    Distribute servers as evenly as possible.

    Example:

    10 servers / 3 racks

    -> 4, 3, 3
    """

    base = total_servers // racks
    remainder = total_servers % racks

    distribution = []

    for i in range(racks):

        servers = base

        if i < remainder:
            servers += 1

        distribution.append(servers)

    return distribution


# ============================================================
# TITLE
# ============================================================

st.title(" Data Center Digital Twin")

st.markdown(
    """
    **Simulate infrastructure changes before applying them
    to the physical data center.**
    """
)

st.markdown(
    """
    <div class="info-box">
     <b>Power</b>
    →
     <b>Heat</b>
    →
     <b>Cooling</b>
    →
     <b>Temperature</b>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# SCENARIO PRESETS
# ============================================================

st.sidebar.header(" Scenario")

scenario = st.sidebar.selectbox(
    "Choose a what-if scenario",
    [
        "Custom Scenario",
        "Add Servers",
        "Cooling Failure",
        "Increase Workload"
    ]
)


# ============================================================
# THREE MAIN COLUMNS
# ============================================================

current_col, model_col, proposed_col = st.columns(
    [1, 1, 1]
)


# ============================================================
# CURRENT SYSTEM
# ============================================================

with current_col:

    st.subheader(" Current System")

    current_servers = st.number_input(
        "Number of servers",
        min_value=1,
        max_value=1000,
        value=10,
        step=1,
        key="current_servers"
    )

    current_workload = st.slider(
        "Average workload (%)",
        min_value=0,
        max_value=100,
        value=50,
        key="current_workload"
    )

    current_racks = st.number_input(
        "Number of racks",
        min_value=1,
        max_value=100,
        value=2,
        step=1,
        key="current_racks"
    )

    current_cooling = st.number_input(
        "Cooling capacity (W)",
        min_value=100,
        max_value=1_000_000,
        value=2500,
        step=100,
        key="current_cooling"
    )

    current_ambient = st.number_input(
        "Ambient temperature (°C)",
        min_value=10.0,
        max_value=50.0,
        value=24.0,
        step=0.5,
        key="current_ambient"
    )


# ============================================================
# MODEL PARAMETERS
# ============================================================

with model_col:

    st.subheader(" Model Parameters")

    cooling_availability = st.slider(
        "Cooling availability (%)",
        min_value=50,
        max_value=100,
        value=90
    )

    thermal_resistance = st.number_input(
        "Thermal resistance (°C/W)",
        min_value=0.001,
        max_value=1.0,
        value=0.05,
        step=0.001,
        format="%.3f"
    )

    thermal_capacitance = st.number_input(
        "Thermal capacitance (J/°C)",
        min_value=100.0,
        max_value=1_000_000.0,
        value=10_000.0,
        step=100.0
    )

    simulation_time = st.slider(
        "Simulation time (seconds)",
        min_value=60,
        max_value=1800,
        value=300,
        step=60
    )

    st.markdown(
        """
        <div class="small-text">
        These parameters describe the thermal behaviour of
        the simulated server room.
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# PROPOSED SYSTEM
# ============================================================

with proposed_col:

    st.subheader(" Proposed System")

    st.caption(
        "Select only the parameters you want to change."
    )

    # --------------------------------------------------------
    # SERVERS
    # --------------------------------------------------------

    change_servers = st.checkbox(
        "Change number of servers",
        key="change_servers"
    )

    if change_servers:

        if scenario == "Add Servers":

            default_servers = min(
                current_servers + 10,
                1000
            )

        else:

            default_servers = current_servers

        proposed_servers = st.number_input(
            "Proposed servers",
            min_value=1,
            max_value=1000,
            value=default_servers,
            step=1,
            key="proposed_servers"
        )

    else:

        proposed_servers = current_servers

        st.write(
            f"Same as current: "
            f"**{current_servers} servers**"
        )


    # --------------------------------------------------------
    # WORKLOAD
    # --------------------------------------------------------

    change_workload = st.checkbox(
        "Change workload",
        key="change_workload"
    )

    if change_workload:

        if scenario == "Increase Workload":

            default_workload = min(
                current_workload + 20,
                100
            )

        else:

            default_workload = current_workload

        proposed_workload = st.slider(
            "Proposed workload (%)",
            min_value=0,
            max_value=100,
            value=default_workload,
            key="proposed_workload"
        )

    else:

        proposed_workload = current_workload

        st.write(
            f"Same as current: "
            f"**{current_workload}%**"
        )


    # --------------------------------------------------------
    # RACKS
    # --------------------------------------------------------

    change_racks = st.checkbox(
        "Change number of racks",
        key="change_racks"
    )

    if change_racks:

        proposed_racks = st.number_input(
            "Proposed racks",
            min_value=1,
            max_value=100,
            value=current_racks,
            step=1,
            key="proposed_racks"
        )

    else:

        proposed_racks = current_racks

        st.write(
            f"Same as current: "
            f"**{current_racks} racks**"
        )


    # --------------------------------------------------------
    # COOLING
    # --------------------------------------------------------

    change_cooling = st.checkbox(
        "Change cooling capacity",
        key="change_cooling"
    )

    if change_cooling:

        if scenario == "Cooling Failure":

            default_cooling = max(
                int(current_cooling * 0.3),
                100
            )

        else:

            default_cooling = current_cooling

        proposed_cooling = st.number_input(
            "Proposed cooling capacity (W)",
            min_value=100,
            max_value=1_000_000,
            value=default_cooling,
            step=100,
            key="proposed_cooling"
        )

    else:

        proposed_cooling = current_cooling

        st.write(
            f"Same as current: "
            f"**{current_cooling:,} W**"
        )


    # --------------------------------------------------------
    # AMBIENT TEMPERATURE
    # --------------------------------------------------------

    change_ambient = st.checkbox(
        "Change ambient temperature",
        key="change_ambient"
    )

    if change_ambient:

        proposed_ambient = st.number_input(
            "Proposed ambient temperature (°C)",
            min_value=10.0,
            max_value=50.0,
            value=current_ambient,
            step=0.5,
            key="proposed_ambient"
        )

    else:

        proposed_ambient = current_ambient

        st.write(
            f"Same as current: "
            f"**{current_ambient} °C**"
        )


# ============================================================
# LOAD BALANCING
# ============================================================

st.divider()

st.header(" Rack Load Balancing")

st.write(
    """
    Distribute servers as evenly as possible across racks
    to reduce uneven rack loading.
    """
)

balance_target = st.radio(
    "Balance",
    [
        "Current system",
        "Proposed system"
    ],
    horizontal=True
)

balance_load = st.button(
    " Load Balance",
    use_container_width=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "balanced_current" not in st.session_state:

    st.session_state.balanced_current = (
        distribute_servers(
            current_servers,
            current_racks
        )
    )


if "balanced_proposed" not in st.session_state:

    st.session_state.balanced_proposed = (
        distribute_servers(
            proposed_servers,
            proposed_racks
        )
    )


# ============================================================
# LOAD BALANCE BUTTON
# ============================================================

if balance_load:

    if balance_target == "Current system":

        st.session_state.balanced_current = (
            distribute_servers(
                current_servers,
                current_racks
            )
        )

    else:

        st.session_state.balanced_proposed = (
            distribute_servers(
                proposed_servers,
                proposed_racks
            )
        )


# ============================================================
# POWER CALCULATIONS
# ============================================================

current_power_per_server, current_power = (
    calculate_power(
        current_servers,
        current_workload
    )
)

proposed_power_per_server, proposed_power = (
    calculate_power(
        proposed_servers,
        proposed_workload
    )
)


# ============================================================
# COOLING
# ============================================================

effective_current_cooling = (
    current_cooling
    * cooling_availability
    / 100
)

effective_proposed_cooling = (
    proposed_cooling
    * cooling_availability
    / 100
)


# ============================================================
# TEMPERATURE
# ============================================================

current_times, current_temperatures = (
    calculate_temperature_response(
        current_power,
        effective_current_cooling,
        current_ambient,
        thermal_resistance,
        thermal_capacitance,
        simulation_time
    )
)


proposed_times, proposed_temperatures = (
    calculate_temperature_response(
        proposed_power,
        effective_proposed_cooling,
        proposed_ambient,
        thermal_resistance,
        thermal_capacitance,
        simulation_time
    )
)


current_final_temperature = current_temperatures[-1]

proposed_final_temperature = proposed_temperatures[-1]


# ============================================================
# RACK TABLES
# ============================================================

st.divider()

rack_col1, rack_col2 = st.columns(2)


with rack_col1:

    st.subheader("Current Rack Distribution")

    current_rows = []

    for i, servers in enumerate(
        st.session_state.balanced_current
    ):

        current_rows.append({
            "Rack": f"Rack {i + 1}",
            "Servers": servers,
            "Power (W)": round(
                servers * current_power_per_server,
                1
            )
        })

    st.dataframe(
        pd.DataFrame(current_rows),
        use_container_width=True,
        hide_index=True
    )


with rack_col2:

    st.subheader("Proposed Rack Distribution")

    proposed_rows = []

    for i, servers in enumerate(
        st.session_state.balanced_proposed
    ):

        proposed_rows.append({
            "Rack": f"Rack {i + 1}",
            "Servers": servers,
            "Power (W)": round(
                servers * proposed_power_per_server,
                1
            )
        })

    st.dataframe(
        pd.DataFrame(proposed_rows),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# RESULTS
# ============================================================

st.divider()

st.header(" Digital Twin Results")


metric1, metric2, metric3, metric4 = st.columns(4)


with metric1:

    st.metric(
        "IT Power",
        f"{current_power:,.0f} W",
        delta=f"{proposed_power-current_power:+,.0f} W"
    )


with metric2:

    st.metric(
        "Heat Generation",
        f"{current_power:,.0f} W",
        delta=f"{proposed_power-current_power:+,.0f} W"
    )


with metric3:

    st.metric(
        "Final Temperature",
        f"{current_final_temperature:.1f} °C",
        delta=f"{proposed_final_temperature-current_final_temperature:+.1f} °C"
    )


with metric4:

    current_margin = (
        effective_current_cooling
        - current_power
    )

    proposed_margin = (
        effective_proposed_cooling
        - proposed_power
    )

    st.metric(
        "Cooling Margin",
        f"{current_margin:,.0f} W",
        delta=f"{proposed_margin-current_margin:+,.0f} W"
    )


# ============================================================
# STATUS
# ============================================================

status1, status2 = st.columns(2)


with status1:

    st.subheader(" Current Status")

    st.write(
        f"Temperature: "
        f"**{current_final_temperature:.2f} °C**"
    )

    st.write(
        f"Status: "
        f"**{temperature_status(current_final_temperature)}**"
    )

    if current_power > effective_current_cooling:

        st.error(
            "Cooling deficit: generated heat exceeds "
            "available cooling."
        )

    else:

        st.success(
            "Cooling capacity is sufficient in the model."
        )


with status2:

    st.subheader(" Proposed Status")

    st.write(
        f"Temperature: "
        f"**{proposed_final_temperature:.2f} °C**"
    )

    st.write(
        f"Status: "
        f"**{temperature_status(proposed_final_temperature)}**"
    )

    if proposed_power > effective_proposed_cooling:

        st.error(
            "Cooling deficit: generated heat exceeds "
            "available cooling."
        )

    else:

        st.success(
            "Cooling capacity is sufficient in the model."
        )


# ============================================================
# TEMPERATURE GRAPH
# ============================================================

st.subheader(" Temperature Response")


temperature_data = pd.DataFrame({
    "Time (seconds)": current_times,
    "Current System": current_temperatures,
    "Proposed System": proposed_temperatures
})


st.line_chart(
    temperature_data,
    x="Time (seconds)",
    y=[
        "Current System",
        "Proposed System"
    ]
)


# ============================================================
# COMPARISON
# ============================================================

st.subheader(" Configuration Comparison")


comparison = pd.DataFrame({

    "Parameter": [
        "Servers",
        "Average workload (%)",
        "Racks",
        "Cooling capacity (W)",
        "Ambient temperature (°C)",
        "IT power (W)",
        "Final temperature (°C)"
    ],

    "Current": [
        current_servers,
        current_workload,
        current_racks,
        current_cooling,
        current_ambient,
        round(current_power, 1),
        round(current_final_temperature, 2)
    ],

    "Proposed": [
        proposed_servers,
        proposed_workload,
        proposed_racks,
        proposed_cooling,
        proposed_ambient,
        round(proposed_power, 1),
        round(proposed_final_temperature, 2)
    ]
})


comparison["Change"] = (
    comparison["Proposed"]
    - comparison["Current"]
)


st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# HOTSPOT ANALYSIS
# ============================================================

st.divider()

st.header(" Rack-Level Hotspot Analysis")


proposed_distribution = (
    st.session_state.balanced_proposed
)


if proposed_distribution:

    proposed_rack_powers = [

        servers * proposed_power_per_server

        for servers in proposed_distribution

    ]

    average_rack_power = (
        sum(proposed_rack_powers)
        / len(proposed_rack_powers)
    )

    hottest_rack = max(
        range(len(proposed_rack_powers)),
        key=lambda i: proposed_rack_powers[i]
    )

    hottest_power = proposed_rack_powers[
        hottest_rack
    ]


    h1, h2, h3 = st.columns(3)


    with h1:

        st.metric(
            "Average rack power",
            f"{average_rack_power:,.0f} W"
        )


    with h2:

        st.metric(
            "Highest rack power",
            f"{hottest_power:,.0f} W"
        )


    with h3:

        st.metric(
            "Highest-load rack",
            f"Rack {hottest_rack + 1}"
        )


    if hottest_power > average_rack_power * 1.25:

        st.warning(
            f" Potential load imbalance detected "
            f"at Rack {hottest_rack + 1}."
        )

    else:

        st.success(
            " Proposed rack distribution is "
            "reasonably balanced."
        )


# ============================================================
# WHAT-IF INSIGHT
# ============================================================

st.divider()

st.header(" What-if Insight")


power_change = (
    proposed_power
    - current_power
)

temperature_change = (
    proposed_final_temperature
    - current_final_temperature
)


if power_change > 0:

    st.write(
        f" Proposed IT power increases by "
        f"**{power_change:,.0f} W**."
    )

elif power_change < 0:

    st.write(
        f" Proposed IT power decreases by "
        f"**{abs(power_change):,.0f} W**."
    )

else:

    st.write(
        " IT power remains unchanged."
    )


if temperature_change > 0:

    st.write(
        f" Simulated final temperature increases by "
        f"**{temperature_change:.2f} °C**."
    )

elif temperature_change < 0:

    st.write(
        f" Simulated final temperature decreases by "
        f"**{abs(temperature_change):.2f} °C**."
    )

else:

    st.write(
        " Simulated final temperature remains unchanged."
    )


# ============================================================
# MODEL ASSUMPTIONS
# ============================================================

with st.expander(" Model assumptions"):

    st.markdown(
        """
### Power

Server power is approximated by:

**P = P_idle + (P_max − P_idle) × workload**

Current prototype assumptions:

- Idle power = 100 W/server
- Maximum power = 300 W/server

### Heat

For this prototype:

**Heat ≈ IT electrical power**

The electrical energy consumed by IT equipment
is ultimately converted to heat.

### Temperature

The room is represented as a simplified lumped
thermal system:

**Cth × dT/dt = Q_heat − Q_cooling − (T − T_ambient)/Rth**

This is a simplified thermal model, not CFD.

### Load balancing

Load balancing currently distributes servers
as evenly as possible across racks.

A future version can balance using real-time
workload, power and temperature measurements.

### Temperature thresholds

The displayed caution, warning and critical
thresholds are prototype thresholds for
demonstration and are not universal
data-center operating limits.
"""
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Data Center Digital Twin • Interactive Engineering Prototype"
)