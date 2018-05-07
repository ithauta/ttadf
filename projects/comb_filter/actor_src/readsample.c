
#include <stdio.h>
#define STATE_READ_WAV_HEADER 0
#define STATE_READ 1
#define STATE_END 2

ACTORSTATE readSample{

    int nb_firings;
    int streamEnd;
    int fms_state;

    #ifdef __ARCH_X86__
    FILE *inputfile_left;
    FILE *inputfile_right;
    #endif

    TTADF_PORT_VAR("o_port_0",left_token,"short");
    //TTADF_PORT_VAR("o_port_1",right_token,"short");

}


INIT readSample(readSample_STATE * state){

    printf("%s INIT\n",state->ttadf_actor_name);
    state->fms_state = STATE_READ_WAV_HEADER;

    #ifdef __ARCH_X86__
    state->inputfile_left = fopen(INPUTFILE_L,"rb");
    if(state->inputfile_left == 0){
        printf("Cannot open file %s\n",INPUTFILE_L);
        TTADF_STOP();
    }
    else{
        printf("File opened: %s\n",INPUTFILE_L);
    }
    /*
    state->inputfile_right = fopen(INPUTFILE_R,"rb");
    if(state->inputfile_right == 0){
        printf("Cannot open file %s\n",INPUTFILE_R);
        TTADF_STOP();
    }
    else{
        printf("File opened: %s\n",INPUTFILE_R);
    }
    */

    #endif

}

FIRE readSample(readSample_STATE * state){



    state->ttadf_nb_firings++;

    static int statusLeftChannel;
    //static int statusRightChannel;


    if(feof(state->inputfile_left)){
        statusLeftChannel = 0;
        printf("Stream left end\n");
    }
    else{
        statusLeftChannel = 1;
    }

    /*
    if(feof(state->inputfile_right)){
        statusRightChannel = 0;
        printf("Stream right end\n");
    }
    else{
        statusRightChannel = 1;
    }
    */

    if( (statusLeftChannel /*&& statusRightChannel*/) == 0){
        //lwpr_print_str("AUDIO INPUT STREAM END\n");
        TTADF_STOP();
    }

    static unsigned char bytesLeftChannel[2];
    static unsigned char bytesRightChannel[2];

    static int output;

    static int i;

    for(i=0;i<2;i++){
        fread(&bytesLeftChannel[i],1,1,state->inputfile_left);
        //fread(&bytesRightChannel[i],1,1,state->inputfile_right);

    }


    TTADF_PORT_WRITE_START("o_port_0",state->left_token);
    *state->left_token = 0;
    *state->left_token = (((short)(bytesLeftChannel[0]))) | ((short)(bytesLeftChannel[1])<<8);
    TTADF_PORT_WRITE_END("o_port_0");



    //if(TTADF_PORT_POPULATION("o_port_1") >2046 || TTADF_PORT_POPULATION("o_port_1") < 0)
    //printf("population o_port_1 %d\n", TTADF_PORT_POPULATION("o_port_1"));

    //TTADF_PORT_WRITE_START("o_port_1",state->right_token);
    //*state->right_token = 0;
    //*state->right_token = (((short)(bytesRightChannel[0]))) | ((short)(bytesRightChannel[1] )<<8);
    //TTADF_PORT_WRITE_END("o_port_1");


}

FINISH readSample(readSample_STATE * state){


    fclose(state->inputfile_left);
    //fclose(state->inputfile_right);
    printf("%s FINISH\n",state->ttadf_actor_name);
    //lwpr_print_str(state->ttadf_actor_name);
    //lwpr_print_str(" FINISH:\n");
    //lwpr_print_str("\tFirings: ");
    //lwpr_print_int(state->ttadf_nb_firings);

    //lwpr_print_str("\n\tStarving: ");
    //lwpr_print_int(state->ttadf_empty);

    //lwpr_print_str("\n\tFull: ");
    //lwpr_print_int(state->ttadf_full);
    //lwpr_print_str("\n");
    return 0;
}
