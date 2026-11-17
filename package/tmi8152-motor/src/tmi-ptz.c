/*
 * tmi-ptz - minimal client for the tmi8152 /dev/motor driver.
 *
 * Uses this driver's own ioctl structs. openipc/motors' ingenic-motor
 * declares struct motor_message without the trailing inversion_state
 * field, so MOTOR_GET_STATUS would write 4 bytes past its buffer.
 *
 *   tmi-ptz -m X Y      relative move by X/Y steps (returns at once)
 *   tmi-ptz -a X Y      absolute move to X/Y
 *   tmi-ptz -s SPEED    set speed (steps/s)
 *   tmi-ptz -r          home (find limits) then return to centre
 *   tmi-ptz -c          go to centre
 *   tmi-ptz -S          stop
 *   tmi-ptz -j          status as JSON
 *   tmi-ptz -w          wait until idle (combine after -m/-a)
 */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#define MOTOR_STOP       0x1
#define MOTOR_RESET      0x2
#define MOTOR_MOVE       0x3
#define MOTOR_GET_STATUS 0x4
#define MOTOR_SPEED      0x5
#define MOTOR_GOBACK     0x6

struct motors_steps { int x; int y; };
struct motor_reset_data {
	unsigned int x_max_steps, y_max_steps, x_cur_step, y_cur_step;
};
struct motor_message {
	int x;
	int y;
	int status; /* enum motor_status: 0 stop, 1 running */
	int speed;
	unsigned int x_max_steps;
	unsigned int y_max_steps;
	unsigned int inversion_state;
};

static int fd = -1;

static int status(struct motor_message *m)
{
	memset(m, 0, sizeof(*m));
	return ioctl(fd, MOTOR_GET_STATUS, m);
}

static void wait_idle(void)
{
	struct motor_message m;
	int i;
	for (i = 0; i < 600; i++) { /* 60 s cap */
		if (status(&m) < 0 || m.status != 1)
			return;
		usleep(100000);
	}
}

static void usage(const char *p)
{
	fprintf(stderr, "usage: %s -m X Y | -a X Y | -s SPEED | -r | -c | -S | -j [-w]\n", p);
	exit(2);
}

int main(int argc, char **argv)
{
	int i, wait = 0, rc = 0;

	fd = open("/dev/motor", O_RDONLY);
	if (fd < 0) {
		perror("/dev/motor");
		return 1;
	}
	if (argc < 2)
		usage(argv[0]);

	for (i = 1; i < argc; i++) {
		const char *a = argv[i];
		if (!strcmp(a, "-m") || !strcmp(a, "-a")) {
			struct motors_steps s;
			if (i + 2 >= argc)
				usage(argv[0]);
			s.x = atoi(argv[++i]);
			s.y = atoi(argv[++i]);
			if (a[1] == 'a') {
				struct motor_message m;
				if (status(&m) < 0) { perror("status"); return 1; }
				s.x -= m.x;
				s.y -= m.y;
			}
			if (ioctl(fd, MOTOR_MOVE, &s) < 0) { perror("move"); rc = 1; }
		} else if (!strcmp(a, "-s")) {
			int sp;
			if (i + 1 >= argc)
				usage(argv[0]);
			sp = atoi(argv[++i]);
			if (ioctl(fd, MOTOR_SPEED, &sp) < 0) { perror("speed"); rc = 1; }
		} else if (!strcmp(a, "-r")) {
			struct motor_reset_data r;
			memset(&r, 0, sizeof(r));
			if (ioctl(fd, MOTOR_RESET, &r) < 0) { perror("reset"); rc = 1; }
		} else if (!strcmp(a, "-c")) {
			struct motor_message m;
			struct motors_steps s;
			if (status(&m) < 0) { perror("status"); return 1; }
			s.x = (int)(m.x_max_steps / 2) - m.x;
			s.y = (int)(m.y_max_steps / 2) - m.y;
			if (ioctl(fd, MOTOR_MOVE, &s) < 0) { perror("move"); rc = 1; }
		} else if (!strcmp(a, "-S")) {
			if (ioctl(fd, MOTOR_STOP, NULL) < 0) { perror("stop"); rc = 1; }
		} else if (!strcmp(a, "-j")) {
			struct motor_message m;
			if (status(&m) < 0) { perror("status"); return 1; }
			printf("{\"x\":%d,\"y\":%d,\"status\":%d,\"speed\":%d,"
			       "\"xmax\":%u,\"ymax\":%u}\n",
			       m.x, m.y, m.status, m.speed, m.x_max_steps, m.y_max_steps);
		} else if (!strcmp(a, "-w")) {
			wait = 1;
		} else {
			usage(argv[0]);
		}
	}
	if (wait)
		wait_idle();
	close(fd);
	return rc;
}
