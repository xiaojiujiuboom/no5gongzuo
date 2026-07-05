#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sdf.h"

#define C_LIGHT 299792458.0
#define M_D_KG 3.3435837724e-27
#define J_PER_MEV 1.602176634e-13

#define EGRID_N 20000
#define EGRID_MIN_MEV 1.0e-4
#define EGRID_MAX_MEV 20.0

static const double stopping_E[] = {
    0.010, 0.020, 0.050, 0.100, 0.200, 0.500, 1.000,
    2.000, 3.000, 5.000, 7.500, 10.000, 15.000, 20.000};
static const double stopping_S[] = {
    1270.0, 1060.0, 795.0, 583.0, 350.0, 159.0, 90.0,
    49.8, 35.0, 23.3, 17.0, 13.8, 10.4, 8.5};
static const int stopping_N = 14;

static double yield_E[EGRID_N];
static double yield_cum[EGRID_N];

static sdf_block_t *find_block(sdf_file_t *h, const char *id) {
    return sdf_find_block_by_id(h, id);
}

static double *read_var(sdf_file_t *h, sdf_block_t *b) {
    if (!b) return NULL;
    h->current_block = b;
    if (sdf_read_point_variable(h)) return NULL;
    return (double *)b->data;
}

static double stopping_power(double E_MeV) {
    double E = E_MeV;
    if (E < stopping_E[0]) E = stopping_E[0];
    if (E > stopping_E[stopping_N - 1]) E = stopping_E[stopping_N - 1];
    double logE = log(E);
    for (int i = 0; i < stopping_N - 1; ++i) {
        if (E >= stopping_E[i] && E <= stopping_E[i + 1]) {
            double x0 = log(stopping_E[i]);
            double x1 = log(stopping_E[i + 1]);
            double y0 = log(stopping_S[i]);
            double y1 = log(stopping_S[i + 1]);
            double f = (logE - x0) / (x1 - x0);
            return exp(y0 + f * (y1 - y0));
        }
    }
    return stopping_S[stopping_N - 1];
}

static double sigma_ddn_cm2(double E_cm_keV) {
    const double E_MIN_KEV = 0.5;
    const double E_MAX_KEV = 4900.0;
    const double BG = 31.3970;
    const double A1 = 5.3701e4;
    const double A2 = 3.3027e2;
    const double A3 = -1.2706e-1;
    const double A4 = 2.9327e-5;
    const double A5 = -2.5151e-9;
    const double MB_TO_CM2 = 1.0e-27;
    if (E_cm_keV < E_MIN_KEV || E_cm_keV > E_MAX_KEV) return 0.0;
    double E = E_cm_keV;
    double S = A1 + E * (A2 + E * (A3 + E * (A4 + E * A5)));
    double sigma_mb = S / (E * exp(BG / sqrt(E)));
    if (!isfinite(sigma_mb) || sigma_mb < 0.0) return 0.0;
    return sigma_mb * MB_TO_CM2;
}

static void init_yield_table(void) {
    const double N_A = 6.02214e23;
    const double rho = 1.06;
    const double molar_mass_cd2 = 12.011 + 2.0 * 2.014;
    const double n_unit = rho * N_A / molar_mass_cd2;
    const double n_D = 2.0 * n_unit;
    for (int i = 0; i < EGRID_N; ++i) {
        double f = (double)i / (double)(EGRID_N - 1);
        yield_E[i] = EGRID_MIN_MEV + f * (EGRID_MAX_MEV - EGRID_MIN_MEV);
    }
    yield_cum[0] = 0.0;
    double prev = n_D * sigma_ddn_cm2(0.5 * yield_E[0] * 1000.0) /
                  stopping_power(yield_E[0]);
    for (int i = 1; i < EGRID_N; ++i) {
        double cur = n_D * sigma_ddn_cm2(0.5 * yield_E[i] * 1000.0) /
                     stopping_power(yield_E[i]);
        double dE = yield_E[i] - yield_E[i - 1];
        yield_cum[i] = yield_cum[i - 1] + 0.5 * (prev + cur) * dE;
        prev = cur;
    }
}

static double thick_yield(double E_MeV) {
    if (!isfinite(E_MeV) || E_MeV <= 0.0) return 0.0;
    if (E_MeV <= yield_E[0]) return 0.0;
    if (E_MeV >= yield_E[EGRID_N - 1]) return yield_cum[EGRID_N - 1];
    double pos = (E_MeV - EGRID_MIN_MEV) *
                 (double)(EGRID_N - 1) / (EGRID_MAX_MEV - EGRID_MIN_MEV);
    int i = (int)floor(pos);
    if (i < 0) return 0.0;
    if (i >= EGRID_N - 1) return yield_cum[EGRID_N - 1];
    double f = pos - (double)i;
    return yield_cum[i] * (1.0 - f) + yield_cum[i + 1] * f;
}

static void usage(const char *argv0) {
    fprintf(stderr,
            "usage: %s --probe D_rear10 --e-min-MeV 0.4 --e-max-MeV 1.6 --bin-width-MeV 0.02 file.sdf...\n",
            argv0);
}

int main(int argc, char **argv) {
    const char *probe = "D_rear10";
    double e_min = 0.4;
    double e_max = 1.6;
    double bin_width = 0.02;
    int first_file = 1;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--probe") == 0 && i + 1 < argc) {
            probe = argv[++i];
            first_file = i + 1;
        } else if (strcmp(argv[i], "--e-min-MeV") == 0 && i + 1 < argc) {
            e_min = atof(argv[++i]);
            first_file = i + 1;
        } else if (strcmp(argv[i], "--e-max-MeV") == 0 && i + 1 < argc) {
            e_max = atof(argv[++i]);
            first_file = i + 1;
        } else if (strcmp(argv[i], "--bin-width-MeV") == 0 && i + 1 < argc) {
            bin_width = atof(argv[++i]);
            first_file = i + 1;
        } else if (argv[i][0] == '-') {
            usage(argv[0]);
            return 2;
        } else {
            first_file = i;
            break;
        }
    }

    if (first_file >= argc || !isfinite(e_min) || !isfinite(e_max) ||
        !isfinite(bin_width) || e_max <= e_min || bin_width <= 0.0) {
        usage(argv[0]);
        return 2;
    }

    int nbins = (int)ceil((e_max - e_min) / bin_width);
    double *hist_w = calloc((size_t)nbins, sizeof(double));
    double *hist_y = calloc((size_t)nbins, sizeof(double));
    if (!hist_w || !hist_y) {
        fprintf(stderr, "allocation_failed\n");
        return 1;
    }
    init_yield_table();

    char idpx[128], idpy[128], idpz[128], idw[128];
    snprintf(idpx, sizeof(idpx), "%s/Px", probe);
    snprintf(idpy, sizeof(idpy), "%s/Py", probe);
    snprintf(idpz, sizeof(idpz), "%s/Pz", probe);
    snprintf(idw, sizeof(idw), "%s/weight", probe);

    double total_w = 0.0;
    double total_y = 0.0;
    int64_t rows_kept = 0;
    int64_t rows_seen = 0;
    double rest = M_D_KG * C_LIGHT * C_LIGHT;

    for (int ai = first_file; ai < argc; ++ai) {
        sdf_file_t *h = sdf_open(argv[ai], 0, SDF_READ, 0);
        if (!h) {
            fprintf(stderr, "open_failed,%s\n", argv[ai]);
            continue;
        }
        sdf_read_header(h);
        sdf_read_blocklist(h);
        sdf_block_t *bpx = find_block(h, idpx);
        sdf_block_t *bpy = find_block(h, idpy);
        sdf_block_t *bpz = find_block(h, idpz);
        sdf_block_t *bw = find_block(h, idw);
        if (!bpx || !bpy || !bpz || !bw) {
            fprintf(stderr, "missing_probe_blocks,%s,%s\n", argv[ai], probe);
            sdf_close(h);
            continue;
        }
        int64_t n = bpx->dims[0];
        double *px = read_var(h, bpx);
        double *py = read_var(h, bpy);
        double *pz = read_var(h, bpz);
        double *w = read_var(h, bw);
        if (!px || !py || !pz || !w || n <= 0) {
            fprintf(stderr, "data_read_failed,%s,%s\n", argv[ai], probe);
            sdf_close(h);
            continue;
        }
        rows_seen += n;
        for (int64_t i = 0; i < n; ++i) {
            if (!(isfinite(px[i]) && isfinite(py[i]) && isfinite(pz[i]) && isfinite(w[i])) ||
                px[i] <= 0.0 || w[i] <= 0.0) {
                continue;
            }
            double p2 = px[i] * px[i] + py[i] * py[i] + pz[i] * pz[i];
            double E = (sqrt(rest * rest + p2 * C_LIGHT * C_LIGHT) - rest) / J_PER_MEV;
            if (E < e_min || E >= e_max) {
                continue;
            }
            int b = (int)floor((E - e_min) / bin_width);
            if (b < 0 || b >= nbins) {
                continue;
            }
            double y = w[i] * thick_yield(E);
            hist_w[b] += w[i];
            hist_y[b] += y;
            total_w += w[i];
            total_y += y;
            ++rows_kept;
        }
        sdf_close(h);
    }

    printf("# probe=%s e_min_MeV=%.9g e_max_MeV=%.9g bin_width_MeV=%.9g rows_seen=%lld rows_kept=%lld total_D_weight=%.17e total_DD_yield_weight=%.17e\n",
           probe, e_min, e_max, bin_width, (long long)rows_seen,
           (long long)rows_kept, total_w, total_y);
    printf("E_low_MeV,E_high_MeV,E_mid_MeV,D_weight_sum,DD_yield_weight_sum\n");
    for (int b = 0; b < nbins; ++b) {
        double lo = e_min + (double)b * bin_width;
        double hi = lo + bin_width;
        double mid = 0.5 * (lo + hi);
        printf("%.9g,%.9g,%.9g,%.17e,%.17e\n", lo, hi, mid, hist_w[b], hist_y[b]);
    }
    free(hist_w);
    free(hist_y);
    return 0;
}
