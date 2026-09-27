#!/usr/bin/python3

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.widgets import SpanSelector
from astropy.io import fits
from datetime import datetime

# --------------------------------------------------
# INPUT FILE
# --------------------------------------------------

txt_file = "lightcurve.txt"

with open(txt_file, "r") as f:

    fits_files = [
        line.strip()
        for line in f
        if line.strip()
    ]

# --------------------------------------------------
# STORE OBSERVATIONS
# --------------------------------------------------

all_obs = []

for file in fits_files:

    try:

        with fits.open(file) as hdul:

            data = hdul[1].data

            hdr0 = hdul[0].header
            hdr1 = hdul[1].header

            cols = data.columns.names

            if "TIME" not in cols:
                continue

            if "RATE" not in cols:
                continue

            time = np.array(
                data["TIME"],
                dtype=float
            )

            rate = np.array(
                data["RATE"],
                dtype=float
            )

            # --------------------------------------------------
            # ERROR
            # --------------------------------------------------

            if "ERROR" in cols:

                error = np.array(
                    data["ERROR"],
                    dtype=float
                )

            elif "RATE_ERR" in cols:

                error = np.array(
                    data["RATE_ERR"],
                    dtype=float
                )

            else:

                error = np.zeros_like(rate)

            # --------------------------------------------------
            # NICER TIME INFO
            # --------------------------------------------------

            mjdrefi = hdr1.get(
                "MJDREFI",
                0.0
            )

            mjdreff = hdr1.get(
                "MJDREFF",
                0.0
            )

            timezero = hdr1.get(
                "TIMEZERO",
                0.0
            )

            mjdref = mjdrefi + mjdreff

            # --------------------------------------------------
            # MJD
            # --------------------------------------------------

            mjd = (
                mjdref
                + (time + timezero) / 86400.0
            )

            # --------------------------------------------------
            # CLEAN
            # --------------------------------------------------

            mask = (
                np.isfinite(mjd)
                & np.isfinite(rate)
            )

            mjd = mjd[mask]

            time = time[mask]

            rate = rate[mask]

            error = error[mask]

            # --------------------------------------------------
            # OBSID FROM HEADER
            # --------------------------------------------------

            obsid = hdr0.get(
                "OBS_ID",
                hdr1.get(
                    "OBS_ID",
                    "Unknown"
                )
            )

            # --------------------------------------------------
            # OBS FOLDER
            # --------------------------------------------------

            obs_folder = os.path.dirname(
                os.path.abspath(file)
            )

            # --------------------------------------------------
            # STORE
            # --------------------------------------------------

            all_obs.append({

                "file": file,

                "obsid": obsid,

                "folder": obs_folder,

                "time": time,

                "mjd": mjd,

                "rate": rate,

                "error": error,

                "mjdref": mjdref,

                "timezero": timezero

            })

    except Exception as e:

        print(f"Failed: {file}")
        print(e)

# --------------------------------------------------
# OUTPUT FILES
# --------------------------------------------------

csv_name = "dip_regions.csv"

log_name = "dip_regions.log"

# --------------------------------------------------
# CREATE CSV
# --------------------------------------------------

if not os.path.exists(csv_name):

    df = pd.DataFrame(columns=[

        "Date",
        "Time",

        "Dip_Name",

        "ObsID",

        "Kind",

        "Classification",

        "Start_MJD",
        "Mid_MJD",
        "Stop_MJD",

        "Start_MET",
        "Mid_MET",
        "Stop_MET",

        "Duration_sec",

        "Depth_counts",

        "Depth_percent"

    ])

    df.to_csv(
        csv_name,
        index=False
    )

# --------------------------------------------------
# PLOT
# --------------------------------------------------

fig, (ax1, ax2) = plt.subplots(

    2,
    1,

    figsize=(14, 8)

)

# --------------------------------------------------
# TOP PANEL
# --------------------------------------------------

for obs in all_obs:

    ax1.errorbar(

        obs["mjd"],

        obs["rate"],

        yerr=obs["error"],

        fmt='.',

        lw=1,

        markersize=3

    )

ax1.set_xlabel("MJD")

ax1.set_ylabel("RATE")

ax1.set_title(
    "All NICER Lightcurves"
)

# --------------------------------------------------
# BOTTOM PANEL
# --------------------------------------------------

ax2.set_xlabel("MJD")

ax2.set_ylabel("RATE")

ax2.set_title(
    "Selected Region"
)

# --------------------------------------------------
# SHORTCUTS
# --------------------------------------------------

print("\n")

print("="*70)

print(
    "NICER DIP SELECTION SHORTCUTS"
)

print("="*70)

print(
    "Mouse Drag  -> Select region"
)

print("")

print("Keyboard:")

print(
    "   a  -> Save NORMAL dip"
)

print(
    "   d  -> Save UNIQUE dip"
)

print(
    "   s  -> Save ONLY image"
)

print(
    "   x  -> Reject selection"
)

print("="*70)

# --------------------------------------------------
# GLOBALS
# --------------------------------------------------

dip_counter = 1

current_selection = None

# --------------------------------------------------
# CLASSIFICATION FUNCTION
# --------------------------------------------------

def classify_dip(depth_percent):

    if depth_percent < 5:

        return "very_shallow"

    elif depth_percent < 12:

        return "shallow"

    else:

        return "deep"

# --------------------------------------------------
# SPAN SELECTOR
# --------------------------------------------------

def onselect(xmin, xmax):

    global current_selection

    ax2.clear()

    for obs in all_obs:

        mjd = obs["mjd"]

        mask = (
            (mjd >= xmin)
            & (mjd <= xmax)
        )

        if np.sum(mask) > 1:

            selected_mjd = mjd[mask]

            selected_rate = obs["rate"][mask]

            selected_error = obs["error"][mask]

            ax2.errorbar(

                selected_mjd,

                selected_rate,

                yerr=selected_error,

                fmt='.',

                lw=1

            )

            ax2.set_xlabel("MJD")

            ax2.set_ylabel("RATE")

            ax2.set_title(

                f"Selected Region : "
                f"{obs['obsid']}"

            )

            plt.draw()

            current_selection = {

                "obs": obs,

                "selected_mjd": selected_mjd,

                "selected_rate": selected_rate,

                "selected_error": selected_error

            }

            print("\nSelection ready")

            print(
                "Press a/d to save"
            )

            print(
                "Press s for image only"
            )

            print(
                "Press x to reject"
            )

            break

# --------------------------------------------------
# SAVE FUNCTION
# --------------------------------------------------

def save_selection(kind="normal"):

    global dip_counter

    global current_selection

    if current_selection is None:

        print(
            "\nNo active selection"
        )

        return

    obs = current_selection["obs"]

    selected_mjd = current_selection[
        "selected_mjd"
    ]

    selected_rate = current_selection[
        "selected_rate"
    ]

    selected_error = current_selection[
        "selected_error"
    ]

    # --------------------------------------------------
    # MJD
    # --------------------------------------------------

    start_mjd = float(
        selected_mjd[0]
    )

    stop_mjd = float(
        selected_mjd[-1]
    )

    mid_mjd = (
        start_mjd + stop_mjd
    ) / 2.0

    # --------------------------------------------------
    # MET
    # --------------------------------------------------

    start_met = (
        (start_mjd - obs["mjdref"])
        * 86400.0
    )

    stop_met = (
        (stop_mjd - obs["mjdref"])
        * 86400.0
    )

    mid_met = (
        (mid_mjd - obs["mjdref"])
        * 86400.0
    )

    duration = (
        stop_met - start_met
    )

    # --------------------------------------------------
    # DEPTH
    # --------------------------------------------------

    persistent = np.percentile(
        selected_rate,
        90
    )

    minimum = np.min(
        selected_rate
    )

    depth_counts = (
        persistent - minimum
    )

    depth_percent = (
        (depth_counts / persistent)
        * 100.0
    )

    # --------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------

    classification = classify_dip(
        depth_percent
    )

    # --------------------------------------------------
    # DUPLICATE CHECK
    # --------------------------------------------------

    duplicate = False

    if os.path.exists(csv_name):

        old_df = pd.read_csv(
            csv_name
        )

        for _, row in old_df.iterrows():

            if (

                row["ObsID"]
                == obs["obsid"]

                and abs(
                    row["Start_MET"]
                    - start_met
                ) < 1

                and abs(
                    row["Stop_MET"]
                    - stop_met
                ) < 1

            ):

                duplicate = True

                break

    if duplicate:

        print(
            "\nDuplicate dip detected"
        )

        return

    # --------------------------------------------------
    # DIP NAME
    # --------------------------------------------------

    dip_name = (
        f"{classification}"
        f"_DIP_{dip_counter}"
    )

    # --------------------------------------------------
    # CREATE GTI
    # --------------------------------------------------

    gti_data = np.array(

        [(start_met, stop_met)],

        dtype=[

            ('START', 'f8'),

            ('STOP', 'f8')

        ]

    )

    with fits.open(obs["file"]) as hdul:

        gti_header = hdul[
            "GTI"
        ].header.copy()

    gti_hdu = fits.BinTableHDU(

        data=gti_data,

        header=gti_header

    )

    gti_hdu.name = 'GTI'

    primary_hdu = fits.PrimaryHDU()

    hdul_new = fits.HDUList([

        primary_hdu,

        gti_hdu

    ])

    # --------------------------------------------------
    # SAVE INSIDE OBS FOLDER
    # --------------------------------------------------

    gti_filename = os.path.join(

        obs["folder"],

        f"{dip_name}_gti.fits"

    )

    hdul_new.writeto(

        gti_filename,

        overwrite=True

    )

    # --------------------------------------------------
    # SAVE INSIDE CWD/OBSID
    # --------------------------------------------------

    local_obs_folder = os.path.join(

        os.getcwd(),

        str(obs["obsid"])

    )

    os.makedirs(

        local_obs_folder,

        exist_ok=True

    )

    local_gti = os.path.join(

        local_obs_folder,

        f"{dip_name}_gti.fits"

    )

    hdul_new.writeto(

        local_gti,

        overwrite=True

    )

    # --------------------------------------------------
    # SAVE IMAGE
    # --------------------------------------------------

    image_name = os.path.join(

        local_obs_folder,

        f"{dip_name}.png"

    )

    fig_save, ax_save = plt.subplots(

        figsize=(8,4)

    )

    ax_save.errorbar(

        selected_mjd,

        selected_rate,

        yerr=selected_error,

        fmt='.',

        lw=1

    )

    ax_save.set_xlabel("MJD")

    ax_save.set_ylabel("RATE")

    ax_save.set_title(

        f"{dip_name} : "
        f"{obs['obsid']}"

    )

    plt.tight_layout()

    fig_save.savefig(

        image_name,

        dpi=300

    )

    plt.close(fig_save)

    # --------------------------------------------------
    # DATE/TIME
    # --------------------------------------------------

    now = datetime.now()

    date_now = now.strftime(
        "%Y-%m-%d"
    )

    time_now = now.strftime(
        "%H:%M:%S"
    )

    # --------------------------------------------------
    # SAVE CSV
    # --------------------------------------------------

    new_row = pd.DataFrame([{

        "Date": date_now,

        "Time": time_now,

        "Dip_Name": dip_name,

        "ObsID": obs["obsid"],

        "Kind": kind,

        "Classification": classification,

        "Start_MJD": start_mjd,

        "Mid_MJD": mid_mjd,

        "Stop_MJD": stop_mjd,

        "Start_MET": start_met,

        "Mid_MET": mid_met,

        "Stop_MET": stop_met,

        "Duration_sec": duration,

        "Depth_counts": depth_counts,

        "Depth_percent": depth_percent

    }])

    new_row.to_csv(

        csv_name,

        mode='a',

        header=False,

        index=False

    )

    # --------------------------------------------------
    # SAVE LOG
    # --------------------------------------------------

    with open(log_name, "a") as log:

        log.write("\n")

        log.write("="*70 + "\n")

        log.write(
            f"Date : {date_now}\n"
        )

        log.write(
            f"Time : {time_now}\n"
        )

        log.write(
            f"Dip Name : {dip_name}\n"
        )

        log.write(
            f"ObsID : {obs['obsid']}\n"
        )

        log.write(
            f"Kind : {kind}\n"
        )

        log.write(
            f"Classification : "
            f"{classification}\n"
        )

        log.write(
            f"Start MJD : "
            f"{start_mjd}\n"
        )

        log.write(
            f"Mid MJD : "
            f"{mid_mjd}\n"
        )

        log.write(
            f"Stop MJD : "
            f"{stop_mjd}\n"
        )

        log.write(
            f"Start MET : "
            f"{start_met}\n"
        )

        log.write(
            f"Mid MET : "
            f"{mid_met}\n"
        )

        log.write(
            f"Stop MET : "
            f"{stop_met}\n"
        )

        log.write(
            f"Duration : "
            f"{duration:.2f} sec\n"
        )

        log.write(
            f"Depth Counts : "
            f"{depth_counts:.3f}\n"
        )

        log.write(
            f"Depth Percent : "
            f"{depth_percent:.2f}\n"
        )

        log.write(
            f"GTI : "
            f"{gti_filename}\n"
        )

        log.write(
            f"Image : "
            f"{image_name}\n"
        )

    print("\nSaved:")

    print(gti_filename)

    print(image_name)

    dip_counter += 1

# --------------------------------------------------
# KEYBOARD SHORTCUTS
# --------------------------------------------------

def onkey(event):

    global current_selection

    # --------------------------------------------------
    # SAVE NORMAL DIP
    # --------------------------------------------------

    if event.key == 'a':

        save_selection(
            kind="normal"
        )

        current_selection = None

    # --------------------------------------------------
    # SAVE UNIQUE DIP
    # --------------------------------------------------

    elif event.key == 'd':

        save_selection(
            kind="unique"
        )

        current_selection = None

    # --------------------------------------------------
    # SAVE IMAGE ONLY
    # --------------------------------------------------

    elif event.key == 's':

        if current_selection is None:

            print(
                "\nNo active selection"
            )

            return

        obs = current_selection["obs"]

        selected_mjd = current_selection[
            "selected_mjd"
        ]

        selected_rate = current_selection[
            "selected_rate"
        ]

        selected_error = current_selection[
            "selected_error"
        ]

        image_folder = os.path.join(

            os.getcwd(),

            str(obs["obsid"])

        )

        os.makedirs(

            image_folder,

            exist_ok=True

        )

        image_name = os.path.join(

            image_folder,

            "preview_DIP.png"

        )

        fig_save, ax_save = plt.subplots(

            figsize=(8,4)

        )

        ax_save.errorbar(

            selected_mjd,

            selected_rate,

            yerr=selected_error,

            fmt='.',

            lw=1

        )

        ax_save.set_xlabel("MJD")

        ax_save.set_ylabel("RATE")

        ax_save.set_title(

            f"Preview : "
            f"{obs['obsid']}"

        )

        plt.tight_layout()

        fig_save.savefig(

            image_name,

            dpi=300

        )

        plt.close(fig_save)

        print(
            "\nPreview image saved:"
        )

        print(image_name)

    # --------------------------------------------------
    # REJECT
    # --------------------------------------------------

    elif event.key == 'x':

        current_selection = None

        ax2.clear()

        ax2.set_xlabel("MJD")

        ax2.set_ylabel("RATE")

        ax2.set_title(
            "Selection Rejected"
        )

        plt.draw()

        print(
            "\nSelection cleared"
        )

# --------------------------------------------------
# CONNECT EVENTS
# --------------------------------------------------

span = SpanSelector(

    ax1,

    onselect,

    'horizontal',

    useblit=True,

    props=dict(

        alpha=0.3,

        facecolor='yellow'

    ),

    interactive=True,

    drag_from_anywhere=True

)

fig.canvas.mpl_connect(

    'key_press_event',

    onkey

)

plt.tight_layout()

plt.show()