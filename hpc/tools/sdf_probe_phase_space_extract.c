#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sdf.h"

#define C_LIGHT 299792458.0
#define M_D_KG 3.3435837724e-27
#define J_PER_MEV 1.602176634e-13

static sdf_block_t *find_block(sdf_file_t *h, const char *id) {
    return sdf_find_block_by_id(h, id);
}

static double *read_var(sdf_file_t *h, sdf_block_t *b) {
    if (!b) return NULL;
    h->current_block = b;
    if (sdf_read_point_variable(h)) return NULL;
    return (double *)b->data;
}

static int read_mesh(sdf_file_t *h, sdf_block_t *b) {
    if (!b) return 1;
    h->current_block = b;
    return sdf_read_point_mesh(h);
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s file.sdf ProbeName output.csv\n", argv[0]);
        return 2;
    }
    const char *fn = argv[1];
    const char *probe = argv[2];
    const char *out = argv[3];
    sdf_file_t *h = sdf_open(fn, 0, SDF_READ, 0);
    if (!h) {
        fprintf(stderr, "open_failed,%s\n", fn);
        return 1;
    }
    sdf_read_header(h);
    sdf_read_blocklist(h);

    char idpx[128], idpy[128], idpz[128], idw[128];
    snprintf(idpx, sizeof(idpx), "%s/Px", probe);
    snprintf(idpy, sizeof(idpy), "%s/Py", probe);
    snprintf(idpz, sizeof(idpz), "%s/Pz", probe);
    snprintf(idw, sizeof(idw), "%s/weight", probe);

    sdf_block_t *bm = find_block(h, probe);
    sdf_block_t *bpx = find_block(h, idpx);
    sdf_block_t *bpy = find_block(h, idpy);
    sdf_block_t *bpz = find_block(h, idpz);
    sdf_block_t *bw = find_block(h, idw);
    if (!bm || !bpx || !bpy || !bpz || !bw) {
        fprintf(stderr, "missing_probe_blocks,%s,%s\n", fn, probe);
        sdf_close(h);
        return 1;
    }
    if (read_mesh(h, bm)) {
        fprintf(stderr, "mesh_read_failed,%s,%s\n", fn, probe);
        sdf_close(h);
        return 1;
    }
    int64_t n = bpx->dims[0];
    double *px = read_var(h, bpx);
    double *py = read_var(h, bpy);
    double *pz = read_var(h, bpz);
    double *w = read_var(h, bw);
    if (!px || !py || !pz || !w || n <= 0 || !bm->grids || bm->ngrids < 3) {
        fprintf(stderr, "data_read_failed,%s,%s\n", fn, probe);
        sdf_close(h);
        return 1;
    }
    double *x = (double *)bm->grids[0];
    double *y = (double *)bm->grids[1];
    double *z = (double *)bm->grids[2];

    FILE *f = fopen(out, "w");
    if (!f) {
        perror(out);
        sdf_close(h);
        return 1;
    }
    fprintf(f, "time_fs,probe,x_um,y_um,z_um,r_um,px,py,pz,weight,E_MeV,theta_y_deg,theta_z_deg,theta_3d_deg\n");
    double rest = M_D_KG * C_LIGHT * C_LIGHT;
    double time_fs = h->time * 1.0e15;
    for (int64_t i = 0; i < n; ++i) {
        if (!(isfinite(px[i]) && isfinite(py[i]) && isfinite(pz[i]) && isfinite(w[i])) ||
            w[i] <= 0.0 || px[i] <= 0.0) {
            continue;
        }
        double p2 = px[i] * px[i] + py[i] * py[i] + pz[i] * pz[i];
        double E = (sqrt(rest * rest + p2 * C_LIGHT * C_LIGHT) - rest) / J_PER_MEV;
        double theta_y = atan2(py[i], px[i]) * 180.0 / M_PI;
        double theta_z = atan2(pz[i], px[i]) * 180.0 / M_PI;
        double theta_3d = atan2(sqrt(py[i] * py[i] + pz[i] * pz[i]), px[i]) * 180.0 / M_PI;
        double x_um = (double)x[i] * 1.0e6;
        double y_um = (double)y[i] * 1.0e6;
        double z_um = (double)z[i] * 1.0e6;
        double r_um = sqrt(y_um * y_um + z_um * z_um);
        fprintf(f, "%.9g,%s,%.9g,%.9g,%.9g,%.9g,%.17g,%.17g,%.17g,%.9e,%.9g,%.9g,%.9g,%.9g\n",
                time_fs, probe, x_um, y_um, z_um, r_um, px[i], py[i], pz[i],
                w[i], E, theta_y, theta_z, theta_3d);
    }
    fclose(f);
    sdf_close(h);
    return 0;
}
