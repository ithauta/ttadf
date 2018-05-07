/*
# Ilkka Hautala
# ithauta@ee.oulu.fi
# Center for Machine Vision and Signal Analysis (CMVS)
# University of Oulu, Finland
# Created 18.1.2017

    memory sync interface between host memory and RTL-shared memory
*/

#ifndef HOST_FIFO_INTERFACE_H_
#define HOST_FIFO_INTERFACE_H_


#include "systemc.h"
#include <fifo.h>


template<int memoryLength, int addrWidth, int dataWidth, int maskL>
SC_MODULE(host_fifo_interface){

    sc_in<bool> clk;
    //sc_in<bool> enable;
    //sc_out<bool> ready;

	sc_out<sc_bv<addrWidth> > addr;
	sc_out<sc_bv<maskL> > bytemask;
	sc_in<sc_bv<dataWidth> > q;
	sc_out<bool> wr_en_x;
	sc_out<bool> mem_en_x;
	sc_out<sc_bv<dataWidth> > d;
	sc_in<bool> waitReq;


    int nbOFifos;
    int nbIFifos;

    uint32_t swapEndianess32b(uint32_t word){

        uint32_t b0,b1,b2,b3;
        uint32_t r;

        b0 = (word & 0x000000ff) << 24u;
        b1 = (word & 0x0000ff00) << 8u;
        b2 = (word & 0x00ff0000) >> 8u;
        b3 = (word & 0xff000000) >> 24u;

        r = b0 | b1 | b2 | b3;
        //r = b3 | b2 | b1 | b0;

        return r;

    }


    void writeMem8b(unsigned char word, uintptr_t address){

        unsigned int bytealign = address & 0x00000003;

        mem_en_x  = false;
        wr_en_x  = false;
        addr = address >> 2;
        unsigned int wordOut = (unsigned int) word;


        //cout << "writeMem8b opp :" << wordOut << " to " << address <<" \n";

        if(bytealign == 0){
            if(maskL == 32){
                //bytemask = "00000000000000000000000011111111";
                bytemask = "11111111111111111111111100000000";
            }
            else{
                bytemask = "0001";
            }

            d = wordOut;
        }
        else if (bytealign == 1){
            if(maskL == 32){
                //bytemask = "00000000000000001111111100000000";
                bytemask = "11111111111111110000000011111111";
            }
            else{
                bytemask = "0010";
            }
            d = wordOut << 8;
        }
        else if (bytealign == 2){
            if(maskL == 32){
                //bytemask = "00000000111111110000000000000000";
                bytemask = "11111111000000001111111111111111";
            }
            else{
                bytemask = "0100";
            }
            d = wordOut << 16;
        }
        else if (bytealign == 3){

            if(maskL == 32){
                //bytemask = "11111111000000000000000000000000";
                bytemask = "00000000111111111111111111111111";
            }
            else{
                bytemask = "1000";
            }
            d = wordOut << 24;
        }
        else{
            cout << "[ERROR] aligment problem when trying 8b write to address '" << address << "'!\n";
        }

        wait();
        while(waitReq.read()==true)wait();

        mem_en_x  = true;
        wr_en_x  = true;
        if(maskL == 32){
                //bytemask = "00000000000000000000000000000000";
                bytemask = "11111111111111111111111111111111";
        }
        else{
            bytemask = "0000";
        }

        addr = 0;
        d = 0;

    }

    void writeMem32b(unsigned int word, uintptr_t address){

        /*
        unsigned char *p = (unsigned char*) &word;

        int i;
        for(i=0;i<4;i++){
            writeMem8b(p[i],address+i);
        }

        */
        //WRITE INIT VALUES TO REAL MEMORY

        unsigned int bytealign = address & 0x00000003;

        //cout << "writeMem32b opp :" << word << "to " << address <<" \n";


        if(bytealign == 0){
            mem_en_x  = false ;
            wr_en_x  = false;
            if(maskL == 32){
                    bytemask = "00000000000000000000000000000000";
                    //bytemask = "11111111111111111111111111111111";
            }
            else{
                bytemask = "1111";
            }
            addr = address >> 2;
            d = word;
            //d = word; //0xffffffff;

        }
        else{
            cout << "[ERROR] aligment problem when trying 32b write to address '" << address << "'!\n";
        }

        wait();
        while(waitReq.read()==true)wait();

        mem_en_x  = true ;
        wr_en_x  = true;

        if(maskL == 32){
                bytemask = "11111111111111111111111111111111";
                //bytemask = "00000000000000000000000000000000";
        }
        else{
            bytemask = "0000";
        }
        addr = 0;
        d = 0;


    }




    unsigned char readMem8b(uintptr_t address){


        unsigned int bytealign = address & 0x00000003;
        mem_en_x  = false ;
        wr_en_x  = true;
        addr = address >> 2;

        wait();
        while(waitReq.read()==true)wait();

        mem_en_x  = true;
        wr_en_x  = true;


        wait();
        while(waitReq.read()==true)wait();

        sc_bv<dataWidth> output;
        output = q;

        if(bytealign == 0){
            return (unsigned char)(output.to_uint()  & 0x000000ff);
        }
        else if (bytealign == 1){
            return (unsigned char)((output.to_uint() & 0x0000ff00) >> 8);

        }
        else if (bytealign == 2){
            return (unsigned char)((output.to_uint() & 0x00ff0000)>> 16);
        }
        else if (bytealign == 3){
            return (unsigned char)((output.to_uint()  & 0xff000000) >> 24);
        }
        else{
            cout << "[ERROR] aligment problem when trying 32b read from address '" << address << "'!\n";
            return 0;
        }

    }

    unsigned int readMem32b(uintptr_t address){
        //WRITE INIT VALUES TO REAL MEMORY
        /*
        int i;
        unsigned int dataOut;
        unsigned char *p = (unsigned char*) &dataOut;
        for(i=0;i<4;i++){
            p[i] = readMem8b(address+i);
        }

        return dataOut;
        */

        //cout << " debug  " << __LINE__  << "\n";
        mem_en_x  = false;
        wr_en_x  = true;
        addr  = address >> 2;

        //cout << " debug  " << __LINE__  << "\n";
        wait();
        while(waitReq.read()==true)wait();

        mem_en_x  = true;
        wr_en_x  = true;

        //cout << " debug  " << __LINE__  << "\n";
        wait();
        while(waitReq.read()==true)wait();

        //cout << " debug  " << __LINE__  << "\n";
        sc_bv<dataWidth> output;
        output = q;

        //cout << " debug  " << __LINE__  << "\n";
        return (unsigned int) output.to_uint();

    }


    uintptr_t ttadf_get_population(uintptr_t witem, uintptr_t ritem, unsigned int maxcap) {
        uintptr_t rd_of, wr_of, w , r;
        rd_of = (ritem >> 31) & 1;
        wr_of = (witem >> 31) & 1;
        r = ritem & ~(1 << 31);
        w = witem & ~(1 << 31);
        if(w > r) return (w-r);
        else if(w < r) return (maxcap-r+w);
        else return ((wr_of ^ rd_of) * maxcap);
    }

    uintptr_t decodeItem(uintptr_t item){
        return item & ~(1 << 31);
    }

    void waitn(int n){
        for(int i=0;i<n;i++) wait();
    }

    void init_output_fifos(){
        int i;
        for(i=0;i<nbOFifos;i++){

            cout << "output fifo "<< i <<" begin init..."<< "\n";

            //cout << " debug  " << __LINE__ << "\n";
            unsigned int capacity = readMem32b( (uintptr_t) &output_fifos_real[i]->capacity);
                output_fifos[i]->capacity = capacity;
                output_fifos_shadow[i].capacity = capacity;
                //cout << " capacity  " << capacity << "\n";
                if (capacity == 0)cout << " capacity  " << capacity;


            uintptr_t buffer_start = readMem32b( (uintptr_t) &output_fifos_real[i]->buffer_start);
                output_fifos[i]->buffer_start = buffer_start;
                output_fifos_shadow[i].buffer_start = buffer_start;


            uintptr_t buffer_end = readMem32b( (uintptr_t) &output_fifos_real[i]->buffer_end);
                output_fifos[i]->buffer_end = buffer_end;
                output_fifos_shadow[i].buffer_end = buffer_end;


            int consuming_stopped = readMem32b( (uintptr_t) &output_fifos_real[i]->consuming_stopped);
                output_fifos[i]->consuming_stopped = consuming_stopped;
                output_fifos_shadow[i].consuming_stopped = consuming_stopped;



            int production_stopped = readMem32b( (uintptr_t) &output_fifos_real[i]->production_stopped);
                output_fifos[i]->production_stopped = production_stopped;
                output_fifos_shadow[i].production_stopped = production_stopped;


            unsigned int write_item_no = readMem32b( (uintptr_t) &output_fifos_real[i]->write_item_no);
                output_fifos[i]->write_item_no = write_item_no;
                output_fifos_shadow[i].write_item_no = write_item_no;


            unsigned int read_item_no =  readMem32b( (uintptr_t) &output_fifos_real[i]->read_item_no);
                output_fifos[i]->read_item_no = read_item_no;
                output_fifos_shadow[i].read_item_no = read_item_no;
            cout << "  OK!\n";
        }
    }

    void init_input_fifos(){
        int i;
        for(i=0;i<nbIFifos;i++){

            cout << "input fifo "<< i <<" begin init... ";

            unsigned int capacity = readMem32b((uintptr_t) (&input_fifos_real[i]->capacity));
                input_fifos[i]->capacity = capacity;
                input_fifos_shadow[i].capacity = capacity;
                if (capacity == 0)cout << " capacity  " << capacity;


            uintptr_t buffer_start = (uintptr_t) readMem32b((uintptr_t) (&input_fifos_real[i]->buffer_start));
                input_fifos[i]->buffer_start = buffer_start;
                input_fifos_shadow[i].buffer_start = buffer_start;


            uintptr_t buffer_end = (uintptr_t) readMem32b((uintptr_t) (&input_fifos_real[i]->buffer_end));
                input_fifos[i]->buffer_end = buffer_end;
                input_fifos_shadow[i].buffer_end = buffer_end;


            int consuming_stopped =  readMem32b((uintptr_t) (&input_fifos_real[i]->consuming_stopped));
                input_fifos[i]->consuming_stopped = consuming_stopped;
                input_fifos_shadow[i].consuming_stopped = consuming_stopped;


            int production_stopped = readMem32b((uintptr_t) (&input_fifos_real[i]->production_stopped));
                input_fifos[i]->production_stopped = production_stopped;
                input_fifos_shadow[i].production_stopped = production_stopped;


            unsigned int write_item_no =  readMem32b((uintptr_t) (&input_fifos_real[i]->write_item_no));
                input_fifos[i]->write_item_no = write_item_no;
                input_fifos_shadow[i].write_item_no = write_item_no;



            unsigned int read_item_no =  readMem32b((uintptr_t) (&input_fifos_real[i]->read_item_no));
                input_fifos[i]->read_item_no = read_item_no;
                input_fifos_shadow[i].read_item_no = read_item_no;

            cout << "OK!\n";
        }
    }

	void sync(){
	    cout << name() << " INITIALIZING FIFOS\n";

	    mem_en_x  = true;
        wr_en_x  = true;

        init_output_fifos();
        init_input_fifos();

        cout << name() << " INIT DONE \n";
         //TODO ADD SIGNAL WHICH WAIT UNTIL ALL IS INIT

        while(1){

            int i;

            for(i=0;i<nbOFifos;i++){

                unsigned int sizeOfToken = (output_fifos_shadow[i].buffer_end - output_fifos_shadow[i].buffer_start) / output_fifos_shadow[i].capacity;
                uintptr_t nb_no_sync_tokens = ttadf_get_population(output_fifos[i]->write_item_no,
                                                             output_fifos_shadow[i].write_item_no,
                                                             output_fifos_shadow[i].capacity*sizeOfToken);
                //bool sync_nb_write_items = false;
                //cout << "write_item = " << output_fifos[i]->write_item_no << "\n";
                //cout << "write_item_shadow = " << output_fifos_shadow[i].write_item_no << "\n";
                //cout << "maxCap = " << output_fifos_shadow[i].capacity*sizeOfToken << "\n";

                //cout << "sizeOfToken = " << sizeOfToken << "\n";
                //cout << "nb_no_sync_tokens = " << nb_no_sync_tokens << "\n";

                unsigned char *p;
                p = (unsigned char *) output_fifos[i];
                p += 128;
                waitn(1);
                if(nb_no_sync_tokens >= sizeOfToken){
                    while(nb_no_sync_tokens){

                        uintptr_t tmp;
                        uintptr_t address = output_fifos_shadow[i].buffer_start+decodeItem(output_fifos_shadow[i].write_item_no);
                        if(nb_no_sync_tokens>=4 && address%4 == 0){
                            unsigned int *int_p;
                            int_p = (unsigned int*) &p[decodeItem(output_fifos_shadow[i].write_item_no)];
                            writeMem32b(*int_p, address);
                            tmp  = decodeItem(output_fifos_shadow[i].write_item_no) + 4;
                            nb_no_sync_tokens -= 4;

                        }

                        else{
                            writeMem8b(p[decodeItem(output_fifos_shadow[i].write_item_no)], address);
                            tmp  = decodeItem(output_fifos_shadow[i].write_item_no) + 1;
                            nb_no_sync_tokens--;
                        }

                        tmp |= output_fifos_shadow[i].write_item_no & 0x80000000UL;
                        if((tmp & ~(1<<31UL)) >= output_fifos_shadow[i].capacity*sizeOfToken){
                            tmp = output_fifos_shadow[i].write_item_no & 0x80000000UL;
                            tmp ^= 1 <<31UL;
                        }
                        output_fifos_shadow[i].write_item_no = 0x00000000FFFFFFFF & tmp;


                    }

                    waitn(1);

                    /*
                    if(i==1){
                    unsigned int write_item_no = readMem32b((uintptr_t) &output_fifos_real[i]->write_item_no);
                    cout << "pre write_item_no = " << write_item_no << "\n";
                    cout << "fifo " << i<<" sync write item " << output_fifos_shadow[i].write_item_no << " at "<< (uintptr_t) &output_fifos_real[i]->write_item_no<<"\n";
                    }
                    */
                    writeMem32b(output_fifos_shadow[i].write_item_no, (uintptr_t) &output_fifos_real[i]->write_item_no);

                }



                uintptr_t population = ttadf_get_population(output_fifos[i]->write_item_no,
                                                output_fifos[i]->read_item_no,
                                                output_fifos[i]->capacity*sizeOfToken);

                int room_left = output_fifos[i]->capacity*sizeOfToken - population;
                waitn(1);

                if(!room_left){
                    unsigned int read_item_no = readMem32b((uintptr_t) &output_fifos_real[i]->read_item_no);
                    output_fifos_shadow[i].read_item_no = read_item_no;
                    output_fifos[i]->read_item_no = read_item_no;
                }

            }


            for(i=0;i<nbIFifos;i++){

                unsigned int sizeOfToken = (input_fifos_shadow[i].buffer_end - input_fifos_shadow[i].buffer_start) / input_fifos_shadow[i].capacity;

                uintptr_t write_item_no;
                write_item_no = (uintptr_t) readMem32b((uintptr_t) (&input_fifos_real[i]->write_item_no));
                input_fifos_shadow[i].write_item_no = write_item_no;
                uintptr_t nb_no_sync_tokens = ttadf_get_population(
                                                             input_fifos_shadow[i].write_item_no,
                                                             input_fifos[i]->write_item_no,
                                                             input_fifos_shadow[i].capacity*sizeOfToken);

                unsigned char *t_p = (unsigned char *) (input_fifos[i]);
                t_p += 128;
                waitn(1);
                if(nb_no_sync_tokens >= sizeOfToken){
                    while(nb_no_sync_tokens){

                        uintptr_t tmp;

                        uintptr_t address = input_fifos[i]->buffer_start+decodeItem(input_fifos[i]->write_item_no);


                        if(nb_no_sync_tokens >= 4 && address%4 == 0){
                            unsigned int *int_p;
                            int_p = (unsigned int*) &t_p[decodeItem(input_fifos[i]->write_item_no)];
                            *int_p =  readMem32b(address);
                            //cout <<"readMem32 b" << *int_p << "\n";
                            tmp  = decodeItem(input_fifos[i]->write_item_no) + 4;
                            nb_no_sync_tokens -= 4;
                        }

                        else{
                            t_p[decodeItem(input_fifos[i]->write_item_no)] =  readMem8b(address);
                            tmp  = decodeItem(input_fifos[i]->write_item_no) + 1;
                            nb_no_sync_tokens--;
                            //cout <<"readMem8b " << (unsigned int)t_p[decodeItem(input_fifos[i]->write_item_no)] << " addr: " << address << "\t@ "<< sc_time_stamp() <<"\n";
                        }

                        tmp |= input_fifos[i]->write_item_no & 0x80000000UL;
                        if((tmp & ~(1<<31UL)) >= input_fifos[i]->capacity*sizeOfToken){
                            tmp = input_fifos[i]->write_item_no & 0x80000000UL;
                            tmp ^= 1 <<31UL;
                        }
                        input_fifos[i]->write_item_no = 0x00000000FFFFFFFF & tmp;
                    }
                }

                waitn(1);

                if(input_fifos_shadow[i].read_item_no != input_fifos[i]->read_item_no){
                    input_fifos_shadow[i].read_item_no = input_fifos[i]->read_item_no;
                    writeMem32b(input_fifos[i]->read_item_no, (uintptr_t)&input_fifos_real[i]->read_item_no);
                }
            }
        }
	}


    SC_HAS_PROCESS(host_fifo_interface);

    host_fifo_interface(sc_module_name name_, unsigned int *intermMemAddr_, unsigned int nbOFifos_, unsigned int *oFifosAddrs_, unsigned int nbIFifos_, unsigned int *iFifosAddrs_)
	{

		SC_CTHREAD(sync,clk.pos());
		//sensitive << clk;

        nbIFifos = nbIFifos_;
        nbOFifos = nbOFifos_;

        input_fifos = new p_fifo[nbIFifos];
        output_fifos = new p_fifo[nbOFifos];

        input_fifos_real = new p_fifo[nbIFifos];
        output_fifos_real = new p_fifo[nbOFifos];

        input_fifos_init = new bool[nbIFifos];
        output_fifos_init = new bool[nbOFifos];

        input_fifos_shadow = new fifoType[nbIFifos];
        output_fifos_shadow = new fifoType[nbOFifos];

        //debugfile.open("host_fifo_debug.txt");

        int i;
        for(i=0; i< nbIFifos; i++){
            input_fifos[i] = (p_fifo) ((uintptr_t) (intermMemAddr_) + iFifosAddrs_[i]);
            input_fifos_real[i] = (p_fifo) (uintptr_t) iFifosAddrs_[i];
            input_fifos_init[i] = false;
            input_fifos_shadow[i] = {0,0,0,0,0,0,0,0,0,0,0};


        }

        for(i=0; i< nbOFifos; i++){
            cout << "mem base p " << intermMemAddr_ << " startoffset: " << oFifosAddrs_[i] << "\n";
            output_fifos[i] = (p_fifo) ((uintptr_t) (intermMemAddr_) + oFifosAddrs_[i]);
            cout << "mem final p " << output_fifos[i] << "\n";
            output_fifos_real[i] =  (p_fifo) (uintptr_t) oFifosAddrs_[i];
            output_fifos_init[i] = false;
            output_fifos_shadow[i] = {0,0,0,0,0,0,0,0,0,0,0};

        }

        cout << "Construction host_fifo_interface " << name() << endl;
	}

	private:

        //ofstream debugfile;

	    p_fifo *input_fifos;
	    p_fifo *output_fifos;
	    p_fifo *input_fifos_real;
	    p_fifo *output_fifos_real;

	    bool *input_fifos_init;
	    bool *output_fifos_init;

	    fifoType *input_fifos_shadow;
	    fifoType *output_fifos_shadow;

};


#endif