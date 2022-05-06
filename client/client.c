
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <unistd.h>
#include <time.h>

#define SERVER_PORT 5432
#define MAX_LINE 256

int main(int argc, char *argv[])
{
    while (1)
    {
        struct hostent *hp;
        struct sockaddr_in sin;
        char *host;
        char buf[MAX_LINE] = {0};
        char buf1[MAX_LINE] = {0};
        int s;
        int len;

        if (argc == 2)
        {
            host = argv[1];
        }
        else
        {
            fprintf(stderr, "usage: simplex-talk host\n");
            exit(1);
        }

        /* translate host name into peer’s IP address */
        hp = gethostbyname(host);
        if (!hp)
        {
            fprintf(stderr, "simplex-talk: unknown host: %s\n", host);
            exit(1);
        }

        /* build address data structure */
        bzero((char *)&sin, sizeof(sin));
        sin.sin_family = AF_INET;
        bcopy(hp->h_addr, (char *)&sin.sin_addr, hp->h_length);
        sin.sin_port = htons(SERVER_PORT);

        /* active open */
        if ((s = socket(PF_INET, SOCK_STREAM, 0)) < 0)
        {
            perror("simplex-talk: socket");
            exit(1);
        }
        if (connect(s, (struct sockaddr *)&sin, sizeof(sin)) < 0)
        {
            perror("simplex-talk: connect");
            close(s);
            exit(1);
        }
        /* main loop: get and send lines of text */
        // while (fgets(buf, MAX_LINE, stdin)) {
        //     buf[MAX_LINE - 1] = '\0';
        //     len = strlen(buf) + 1;
        //     send(s, buf, len, 0);
        // }

        recv(s, buf, MAX_LINE, 0);
        fputs(buf, stdout);
        bzero(buf, MAX_LINE);
        int n;

        close(s);
    }
}