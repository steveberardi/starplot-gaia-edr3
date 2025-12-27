def tycho2_bv_v(mag_bt, mag_vt) -> tuple[float, float]:
    """
    Calculates B-V and Johnson V magnitude from Tycho-2 data.

    From Tycho-2 Readme:
        Note (7):
        Blank when no magnitude is available. Either BTmag or VTmag is
        always given. Approximate Johnson photometry may be obtained as:

            V   = VT - 0.090 * (BT-VT)
            B-V = 0.850 * (BT-VT)

        Consult Sect 1.3 of Vol 1 of "The Hipparcos and Tycho Catalogues",
        ESA SP-1200, 1997, for details.
    """

    if mag_bt is None or mag_vt is None:
        return None, mag_vt or mag_bt

    bv = 0.850 * (mag_bt - mag_vt)
    mag = mag_vt - 0.09 * (mag_bt - mag_vt)

    return bv, mag


def get_bt(phot_g_mean_mag, bp_rp) -> float:
    """
    Calculates BT from Gaia EDR3 data: phot_g_mean_mag and bp_rp

    Coefficients obtained from Table 5.6 at:
    https://gea.esac.esa.int/archive/documentation/GEDR3/Data_processing/chap_cu5pho/cu5pho_sec_photSystem/cu5pho_ssec_photRelations.html
    """
    g_bt = (
        (-0.8547 * bp_rp)
        + (0.1244 * bp_rp**2)
        - (0.9085 * bp_rp**3)
        + (0.4843 * bp_rp**4)
        - (0.06814 * bp_rp**5)
        - 0.004288
    )
    bt = phot_g_mean_mag - g_bt
    return bt


def get_vt(phot_g_mean_mag, bp_rp):
    """
    Calculates VT from Gaia EDR3 data: phot_g_mean_mag and bp_rp

    Coefficients obtained from Table 5.6 at:
    https://gea.esac.esa.int/archive/documentation/GEDR3/Data_processing/chap_cu5pho/cu5pho_sec_photSystem/cu5pho_ssec_photRelations.html
    """
    g_vt = (-0.0682 * bp_rp) - (0.2387 * bp_rp**2) + (0.02342 * bp_rp**3) - 0.01077
    vt = phot_g_mean_mag - g_vt
    return vt


def get_bv_v(phot_g_mean_mag, bp_rp) -> tuple[float, float]:
    bt = get_bt(phot_g_mean_mag, bp_rp)
    vt = get_vt(phot_g_mean_mag, bp_rp)
    return tycho2_bv_v(mag_bt=bt, mag_vt=vt)
