#include <stdio.h>
#include "lwpr.h"

#define STATE_BYPASS_HEADER 0
#define STATE_FILTER 1
#define STATE_END 2

ACTORSTATE combfilter{

    int nb_firings;
    int streamEnd;
    int fms_state;
    int delayline[DELAYLINELEN];
    int headerByteNo;

    int xn;
    int wn;
    int yn;

    TTADF_PORT_VAR("i_port_0",sample,"short");
    TTADF_PORT_VAR("o_port_0",filteredSample,"short");

    TTADF_PORT_VECTOR_VAR("i_port_0",sample_vec,"short",DELAYLINELEN);
    TTADF_PORT_VECTOR_VAR("o_port_0",filteredSample_vec,"short",DELAYLINELEN);


}


INIT combfilter(combfilter_STATE * state) {

    //printf("%s INIT",state->ttadf_actor_name);

    state->nb_firings = 0;
    state->streamEnd = 0;
    state->fms_state = STATE_BYPASS_HEADER;
    state->headerByteNo = 0;

    for(int i=0; i<DELAYLINELEN;i++){
        state->delayline[i] = 0;
    }
    state->sample = 0;
    state->xn = 0;
    state->wn = 0;
    state->yn = 0;

}

FIRE combfilter(combfilter_STATE * state){

    state->ttadf_nb_firings++;


    static int i;


    if(TTADF_FIFO_IS_PRODUCTION_STOPPED("i_port_0")){
        TTADF_STOP();
    }

    if( state->fms_state == STATE_BYPASS_HEADER){

            TTADF_PORT_READ_START("i_port_0",state->sample);
            TTADF_PORT_WRITE_START("o_port_0",state->filteredSample);

            *state->filteredSample = *state->sample;

            TTADF_PORT_WRITE_END("o_port_0");
            TTADF_PORT_READ_END("i_port_0");
            state->headerByteNo = state->headerByteNo + 1;
            if(state->headerByteNo == 44){
                state->fms_state = STATE_FILTER;
            }

    }

    else{


        /*
        TTADF_PORT_MULTIRATE_READ_START("i_port_0",state->sample,DELAYLINELEN);
        TTADF_PORT_MULTIRATE_WRITE_START("o_port_0",state->filteredSample,DELAYLINELEN);

        for(i=0; i<DELAYLINELEN; i++){

            state->xn = (int) *state->sample;

            int oldest;
            if(i==(DELAYLINELEN-1)) oldest = state->delayline[0];
            else oldest = state->delayline[i+1];

            state->wn = (state->xn) + ((oldest*A48)>>3);
            state->delayline[i] = state->wn;
            state->yn = ((state->wn*B0)>>3) + ((oldest*B48)>>3);

            *state->filteredSample = (short) state->yn;

            TTADF_PORT_READ_UPDATE("i_port_0",state->sample);
            TTADF_PORT_WRITE_UPDATE("o_port_0",state->filteredSample);

        }

        TTADF_PORT_MULTIRATE_READ_END("i_port_0");
        TTADF_PORT_MULTIRATE_WRITE_END("o_port_0");
        */

        TTADF_PORT_VECTOR_READ_START("i_port_0",state->sample_vec,DELAYLINELEN);
        TTADF_PORT_VECTOR_WRITE_START("o_port_0",state->filteredSample_vec,DELAYLINELEN);

        for(i=0; i<DELAYLINELEN; i++){

            state->xn = (int) *state->sample_vec[i];

            int oldest;
            if(i==(DELAYLINELEN-1)) oldest = state->delayline[0];
            else oldest = state->delayline[i+1];

            state->wn = (state->xn) + ((oldest*A48)>>3);
            state->delayline[i] = state->wn;
            state->yn = ((state->wn*B0)>>3) + ((oldest*B48)>>3);

            *state->filteredSample_vec[i] = (short) state->yn;

        }

        TTADF_PORT_VECTOR_READ_END("i_port_0");
        TTADF_PORT_VECTOR_WRITE_END("o_port_0");

    }



}

FINISH combfilter(combfilter_STATE * state){

      //printf("%s FINISH",state->ttadf_actor_name);
    //printf("%s FINISH:\n",state->ttadf_actor_name);
    //printf("\tFirings: %d\n ",state->ttadf_nb_firings);

//    lwpr_print_str("\n\tStarving: ");
//    lwpr_print_str("\n\t\ti_port_0: ");
//    lwpr_print_int(TTADF_GET_PORT("i_port_0")->starving);
//    lwpr_print_str("\n\tFull: ");
//    lwpr_print_str("\n\t\to_port_0: ");
//    lwpr_print_int(TTADF_GET_PORT("o_port_0")->full);
//    lwpr_print_str("\n");
    return 0;
}
