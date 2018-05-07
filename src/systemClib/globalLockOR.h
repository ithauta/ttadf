#include <systemc.h>
#include <iostream>

template<int glockinputs = 1>
SC_MODULE(globalLockOR)
{

    sc_in<bool> glocks[glockinputs];

	sc_out<bool> glock;


    void glockOR()
    {
        bool glockval = false;

        int i;
        for(i=0; i<glockinputs; i++){
            if(glocks[i] == true){
                glockval = true;
                //cout << name() << " glock enabled\n";
                break;
            }
        }

        glock = glockval;

    }

    SC_CTOR(globalLockOR){


        SC_METHOD(glockOR);
        int i;

        for(i=0;i<glockinputs;i++){
            sensitive << glocks[i];
        }




    }

};