#include <cstdio>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <unistd.h>
#include <cstdlib>
#include <iostream>
#include <cstring>
#include <fstream>

constexpr size_t BUFSIZE = 1024;

int initCmd( int fd, std::string fname){
    char buffer[BUFSIZE];
    std::ifstream ifs( fname);
    std::string line;
    
    while( std::getline( ifs, line)){
        std::cout << line << std::endl;
        send( fd, buffer, strlen(buffer), 0);
        usleep(100000);
    }

    // strcpy( buffer, "*IDN?\n");
    // send( fd, buffer, strlen(buffer), 0);

    return 0;
}

int main( int argc, char **argv){
    int fd;
    struct sockaddr_in serv_addr;
    struct hostent *server;

    char buffer[BUFSIZE];
    int recv_size;

    fd = socket( AF_INET, SOCK_STREAM, 0);
    if( fd < 0 ){
        std::cout << "[ERR] Failed to open socket" << std::endl;
        return EXIT_FAILURE;
    }

    server = gethostbyname( "127.0.0.1");
    if( server == NULL ){
        std::cout << "[ERR] Failed to get host name" << std::endl;
        return EXIT_FAILURE;
    }
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(4000);
    serv_addr.sin_addr.s_addr = *((unsigned long *)server->h_addr);


    if ( connect( fd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0){
        std::cout << "[ERR] Failed to connect to host" << std::endl;
        return EXIT_FAILURE;
    }

    struct timeval tv;
    tv.tv_sec = 1;
    tv.tv_usec = 0;
    setsockopt( fd, SOL_SOCKET, SO_RCVTIMEO, (const char *)&tv, sizeof(struct timeval));


    strcpy( buffer, "*CLS;*CLS;*CLS;\n");
    send( fd, buffer, strlen(buffer), 0);

    strcpy( buffer, "*IDN?\n");
    send( fd, buffer, strlen(buffer), 0);
    // usleep(1);
    recv_size = recv( fd, buffer, BUFSIZE, 0);
    buffer[recv_size] = NULL;
    std::cout << buffer << std::endl;

    strcpy( buffer, "*RST\n");
    send( fd, buffer, strlen(buffer), 0);
    strcpy( buffer, "*OPC?\n");
    send( fd, buffer, strlen(buffer), 0);
    recv_size = recv( fd, buffer, BUFSIZE, 0);
    buffer[recv_size] = NULL;
    std::cout << buffer << std::endl;

    initCmd( fd, "init.cmd");
    
    usleep(1000);

    strcpy( buffer, "*OPC?\n");
    send( fd, buffer, strlen(buffer), 0);
    recv_size = recv( fd, buffer, BUFSIZE, 0);
    buffer[recv_size] = NULL;
    std::cout << buffer << std::endl;


    strcpy( buffer, "ACQ:STATE ON\n");
    send( fd, buffer, strlen(buffer), 0);
    strcpy( buffer, "*OPC?\n");
    send( fd, buffer, strlen(buffer), 0);
    recv_size = recv( fd, buffer, BUFSIZE, 0);
    buffer[recv_size] = NULL;
    int evtnum = atoi( buffer);
    std::cout << "[INFO] Acq " << evtnum << std::endl;
    usleep(10000);
    strcpy( buffer, "ALLEV?\n");
    send( fd, buffer, strlen(buffer), 0);
    recv_size = recv( fd, buffer, BUFSIZE, 0);
    buffer[recv_size] = NULL;
    std::cout << buffer << std::endl;

    usleep(10000);
    strcpy( buffer, "CURVE?\n");
    send( fd, buffer, strlen(buffer), 0);
    recv_size = recv( fd, buffer, BUFSIZE, 0);
    buffer[recv_size] = NULL;
    printf("[CURV] " );
    for( int i = 0; i < recv_size; i++ ) printf(" %x", buffer[i]);



    close( fd);
    return EXIT_SUCCESS;
}

