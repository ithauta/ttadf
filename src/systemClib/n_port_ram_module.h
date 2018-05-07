/*
# Ilkka Hautala
# ithauta@ee.oulu.fi
# Center for Machine Vision and Signal Analysis (CMVS)
# University of Oulu, Finland
# Createad 7.5.2017

    SystemC implementation of N port ram module
*/

#ifndef N_PORT_RAM_MODULE_H_
#define N_PORT_RAM_MODULE_H_

#include <stdio.h>
#include <stdlib.h>
#include <algorithm>
#include <bitset>
#include <string>
#include <vector>
#include "systemc.h"


template<int memoryLength, int addrWidth, int dataWidth, int nbPorts, bool initMem >
SC_MODULE(n_port_ram_module){

	sc_in<bool> clk;
	sc_in<sc_bv<addrWidth> > addr[nbPorts];
	sc_in<sc_bv<dataWidth/8> > bytemask[nbPorts];
	sc_out<sc_bv<dataWidth> > dataOut[nbPorts];
	sc_in<bool> wr_en_x[nbPorts];
	sc_in<bool> mem_en_x[nbPorts];
	sc_in<sc_bv<dataWidth> > dataIn[nbPorts];

    sc_bv<dataWidth> memory[memoryLength];
 
    //https://stackoverflow.com/questions/236129/split-a-string-in-c
    template<typename Out>
    void split(const std::string &s, char delim, Out result) {
        std::stringstream ss;
        ss.str(s);
        std::string item;
        while (std::getline(ss, item, delim)) {
            *(result++) = item;
        }
    }

    std::vector<std::string> split(const std::string &s, char delim) {
        std::vector<std::string> elems;
        split(s, delim, std::back_inserter(elems));
        return elems;
    }

    void mem_init(const char* initFileName){

        ifstream initFile;
        initFile.open(initFileName,ifstream::in);

        char *memWord = new char[35];
        memWord[32] = '\0';


        int i = 0;
        int memAddr = 0;
        memWord[0] = initFile.get();
        i++;
        while(initFile.good()){
            if(i==32){

                memory[memAddr] = memWord;
                i=0;
                memWord[i] = initFile.get(); //this should be a newline character
                memAddr++;
            }
            memWord[i] = initFile.get();
            i++;
        }

        delete[]memWord;
        initFile.close();

    }

    int parseMIFline(std::string line, unsigned int *address, unsigned int *data){

        std::vector<std::string> x = split(line, ':');
        std::vector<std::string> y;

        if(x.size()>1){
            y = split(x[1],';');
        }

        if(y.size()>1){
            std::string::iterator end_pos = std::remove(x[0].begin(), x[0].end(), ' ');
            x[0].erase(end_pos, x[0].end());

            end_pos = std::remove(y[0].begin(), y[0].end(), ' ');
            y[0].erase(end_pos, y[0].end());

            std::stringstream ss;
            ss << std::hex <<x[0];
            ss >> *address;

            *data = (unsigned int) std::bitset<32>(y[0]).to_ulong();
            return 0;
        }

        return 1;
    }

    void mem_init_mif(const char * mifFileName){

        std::ifstream fin;
        fin.open(mifFileName);

        std::string line;

        unsigned int address = 0;
        unsigned int data = 0;
        int nvalid;

        if(fin.is_open()){
            while(getline(fin,line)){
                nvalid = parseMIFline(line,&address,&data);
                if(!nvalid){
                    memory[address/4] = data;
                }
            }
            cout << "Memory initialization of "<< name() <<" done!\n";
            fin.close();
        }
        else{
            cout << "Cannot open memory initialization file "<< mifFileName <<"!\n";
        }
    }

	void mem_write()
	{


        int port;

        for(port=0;port<nbPorts;port++){

            sc_bv<addrWidth> addr_t;
            sc_bv<dataWidth> data_t;
            sc_bv<dataWidth/8> bytemask_t;


            if(wr_en_x[port] == false && mem_en_x[port] == false){
                addr_t = addr[port].read();
                bytemask_t = bytemask[port].read();

                if(addr_t.to_uint()>= 0 && addr_t.to_uint() < memoryLength){
                    int i;
                    for(i=0; i<dataWidth/8; i++){
                      if(bytemask_t[i] == true){
                            data_t = dataIn[port].read();
                            memory[addr_t.to_uint()].range(8*i+7,8*i) = data_t.range(8*i+7,8*i);
                        }
                    }
                }
                else{
                    cout << "WARNING WRITE ADDRESS ERROR!\n";
                }
            }

            if(mem_en_x[port] == false && wr_en_x[port] == true){
                addr_t = addr[port].read();

                if(addr_t.to_uint() >= 0 && addr_t.to_uint()<memoryLength){
                    dataOut[port] = memory[addr_t.to_uint()];
                }
                else{
                    cout << "WARNING READ ADDRESS ERROR!\n";
                }
            }
        }

	}


	SC_HAS_PROCESS(n_port_ram_module); n_port_ram_module(sc_module_name nm, const char *initFileName): sc_module(nm)
	{
		cout << "Constructing "<< nbPorts << " port RAM " << name() << endl;

		mem_init_mif(initFileName);


		SC_METHOD(mem_write);
		sensitive << clk.pos();

	}
};


#endif /* DUALPORTMEM_HH_ */
