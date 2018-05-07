#include <stdio.h>

#define STATE_WRITE_WAV_HEADER 0
#define STATE_READ 1
#define STATE_END 2

ACTORSTATE writeSample{

    int nb_firings;
    int streamEnd;
    int fms_state;

    #ifdef __ARCH_X86__
    FILE *outputfile_left;
    FILE *outputfile_right;
    #endif


    TTADF_PORT_VAR("i_port_0",left_token,"short");
    //TTADF_PORT_VAR("i_port_1",right_token,"short");
}


INIT writeSample(writeSample_STATE * state){

    printf("%s INIT\n",state->ttadf_actor_name);

    state->nb_firings = 0;
    state->streamEnd = 0;
    state->fms_state = STATE_WRITE_WAV_HEADER;


    state->outputfile_left = fopen(OUTPUTFILE_L,"w");
    //state->outputfile_right = fopen(OUTPUTFILE_R,"w");


}

FIRE writeSample(writeSample_STATE * state){


    TTADF_PORT_READ_START("i_port_0",state->left_token);
    //TTADF_PORT_READ_START("i_port_1",state->right_token);

/*
    char t1 = ((char *)(state->left_token)[0]);
    char t2 = ((char *)(state->left_token)[1]);

    fprintf(state->outputfile_left, "%d\n", t1);
    fprintf(state->outputfile_left, "%d\n", t2);

    t1 = ((char *)(state->right_token)[0]);
    t2 = ((char *)(state->right_token)[1]);

    fprintf(state->outputfile_right, "%d\n", t1);
    fprintf(state->outputfile_right, "%d\n", t2);

*/
    //printf("%d\n",*state->left_token);
    //fprintf(state->outputfile_left, "%x\n", *state->left_token);
    fwrite(state->left_token,2,1,state->outputfile_left);
    //fwrite(state->right_token,2,1,state->outputfile_right);
    state->ttadf_nb_firings++;



    TTADF_PORT_READ_END("i_port_0");
    //TTADF_PORT_READ_END("i_port_1");

}

FINISH writeSample(writeSample_STATE * state){

    //fclose(state->outputfile_right);
    fclose(state->outputfile_left);
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
