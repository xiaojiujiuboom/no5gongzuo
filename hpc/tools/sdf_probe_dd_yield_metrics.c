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

/* NIST PSTAR same-velocity D-in-CD2 proxy; see data/stopping_D_in_CD2.csv. */
static const double stopping_E[] = {
    0.002, 0.005, 0.010, 0.020, 0.050, 0.100, 0.200,
    0.500, 1.000, 2.000, 3.000, 5.000, 7.500, 10.000,
    15.000, 20.000, 30.000};
static const double stopping_S[] = {
    253.34, 343.016, 458.98, 632.29, 907.996, 1109.82,
    1119.36, 761.822, 493.218, 306.658, 228.96, 156.35,
    114.374, 91.1812, 65.9108, 52.2156, 37.5028};
static const int stopping_N = 17;

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

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s [--e-min-MeV value] file.sdf...\n", argv[0]);
        return 2;
    }
    double e_min_MeV = 0.0;
    int first_file = 1;
    if (argc >= 4 && strcmp(argv[1], "--e-min-MeV") == 0) {
        e_min_MeV = atof(argv[2]);
        if (!isfinite(e_min_MeV) || e_min_MeV < 0.0) {
            fprintf(stderr, "invalid --e-min-MeV value: %s\n", argv[2]);
            return 2;
        }
        first_file = 3;
    }
    if (first_file >= argc) {
        fprintf(stderr, "usage: %s [--e-min-MeV value] file.sdf...\n", argv[0]);
        return 2;
    }
    init_yield_table();
    const char *probes[] = {"D_rear02", "D_rear05", "D_rear10", "D_rear15", "D_rear20"};
    const int nprobes = 5;
    printf("sdf,time_fs,probe,E_min_MeV,n_macro,weight_sum,E_weighted_mean_MeV,E_max_MeV,ddn_yield_sum,ddn_yield_per_weight\n");
    for (int ai = first_file; ai < argc; ++ai) {
        const char *fn = argv[ai];
        sdf_file_t *h = sdf_open(fn, 0, SDF_READ, 0);
        if (!h) {
            fprintf(stderr, "open_failed,%s\n", fn);
            continue;
        }
        sdf_read_header(h);
        sdf_read_blocklist(h);
        double time_fs = h->time * 1.0e15;
        const char *base = strrchr(fn, '/');
        base = base ? base + 1 : fn;
        for (int pi = 0; pi < nprobes; ++pi) {
            char idpx[128], idpy[128], idpz[128], idw[128];
            snprintf(idpx, sizeof(idpx), "%s/Px", probes[pi]);
            snprintf(idpy, sizeof(idpy), "%s/Py", probes[pi]);
            snprintf(idpz, sizeof(idpz), "%s/Pz", probes[pi]);
            snprintf(idw, sizeof(idw), "%s/weight", probes[pi]);
            sdf_block_t *bpx = find_block(h, idpx);
            sdf_block_t *bpy = find_block(h, idpy);
            sdf_block_t *bpz = find_block(h, idpz);
            sdf_block_t *bw = find_block(h, idw);
            if (!bpx || !bpy || !bpz || !bw) {
                printf("%s,%.9g,%s,%.9g,0,0,nan,nan,0,0\n", base, time_fs, probes[pi], e_min_MeV);
                continue;
            }
            int64_t n = bpx->dims[0];
            double *px = read_var(h, bpx);
            double *py = read_var(h, bpy);
            double *pz = read_var(h, bpz);
            double *w = read_var(h, bw);
            if (!px || !py || !pz || !w || n <= 0) {
                printf("%s,%.9g,%s,%.9g,0,0,nan,nan,0,0\n", base, time_fs, probes[pi], e_min_MeV);
                continue;
            }
            double rest = M_D_KG * C_LIGHT * C_LIGHT;
            double wsum = 0.0;
            double Esum = 0.0;
            double Emax = -1.0;
            double ysum = 0.0;
            int64_t kept = 0;
            for (int64_t i = 0; i < n; ++i) {
                if (!(isfinite(px[i]) && isfinite(py[i]) && isfinite(pz[i]) && isfinite(w[i])) ||
                    px[i] <= 0.0 || w[i] <= 0.0) {
                    continue;
                }
                double p2 = px[i] * px[i] + py[i] * py[i] + pz[i] * pz[i];
                double E = (sqrt(rest * rest + p2 * C_LIGHT * C_LIGHT) - rest) / J_PER_MEV;
                if (E < e_min_MeV) {
                    continue;
                }
                double y = thick_yield(E);
                wsum += w[i];
                Esum += w[i] * E;
                ysum += w[i] * y;
                if (E > Emax) Emax = E;
                ++kept;
            }
            if (kept <= 0 || wsum <= 0.0) {
                printf("%s,%.9g,%s,%.9g,0,0,nan,nan,0,0\n", base, time_fs, probes[pi], e_min_MeV);
            } else {
                printf("%s,%.9g,%s,%.9g,%lld,%.9e,%.9g,%.9g,%.9e,%.9e\n",
                       base, time_fs, probes[pi], e_min_MeV, (long long)kept, wsum,
                       Esum / wsum, Emax, ysum, ysum / wsum);
            }
        }
        sdf_close(h);
    }
    return 0;
}
