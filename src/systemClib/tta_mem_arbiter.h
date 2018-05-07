
/*

# Ilkka Hautala
# ithauta@ee.oulu.fi
# Center for Machine Vision and Signal Analysis (CMVS)
# University of Oulu, Finland

    SystemC implementation of Memory arbiter
    Based on VHDL implementation of avalon mem arbiter authored by AK (TCE project)

*/

#ifndef TTA_MEM_ARBITER_H_
#define TTA_MEM_ARBITER_H_


#include <systemc.h>


template<int ports_g, int addrw_g, int dataw_g, int memLen>
SC_MODULE(tta_mem_arbiter)
{

    /*MODULE INPUT INTERFACE */
    sc_in<bool> clk;
    sc_in<bool> rst_n;
    sc_in<sc_bv<dataw_g/8> > bit_wr_x[ports_g];
    sc_in<bool> en_x[ports_g];
    sc_in<bool>  wr_x[ports_g];
    sc_in<sc_bv<dataw_g> > d[ports_g];
    sc_in<sc_bv<addrw_g> > addr[ports_g];

    /*MODULE OUTPUT INTERFACE */
    sc_out<sc_bv<dataw_g> > q[ports_g];
    sc_out<bool> waitrequest[ports_g];


    /*RAM MODULE INTERFACE SIGNALS*/
    sc_out<bool> ram_en_x;
    sc_out<bool> ram_wr_x;
    sc_out<sc_bv<dataw_g> > ram_d;
    sc_in<sc_bv<dataw_g> > ram_q;
    sc_out<sc_bv<dataw_g/8> > ram_bit_wr_x;
    sc_out<sc_bv<addrw_g> > ram_addr;


    /*MODULE INTERNAL SIGNALS */
    sc_signal<bool> input_latch_load;
    sc_signal<bool> latch_en_x[ports_g], latch_en_x_r[ports_g];
    sc_signal<bool> latch_wr_x[ports_g], latch_wr_x_r[ports_g];

    sc_signal<sc_bv<dataw_g/8> > latch_bit_wr_x[ports_g];
    sc_signal<sc_bv<dataw_g/8> > latch_bit_wr_x_r[ports_g];
    sc_signal<sc_bv<dataw_g> > latch_d[ports_g];
    sc_signal<sc_bv<dataw_g> > latch_d_r[ports_g];
    sc_signal<sc_bv<addrw_g> > latch_addr[ports_g];
    sc_signal<sc_bv<addrw_g> > latch_addr_r[ports_g];

    sc_signal<bool> output_latch_load;



    sc_signal<sc_bv<dataw_g> > q_v[ports_g];
    sc_signal<sc_bv<dataw_g> > q_v_r[ports_g];

    sc_signal<int> selected_port;
    sc_signal<bool> selected_port_mask_x[ports_g];
    sc_signal<bool> selected_port_mask_x_r[ports_g];

    sc_signal<bool> wait_rq_r_in [ports_g];
    sc_signal<bool> wait_rq_r [ports_g];


    int pointer;

    void priority_encoder(){
        ram_en_x = true;
        selected_port = 0;

        int i;
        for(i=0; i<ports_g; i++){
            selected_port_mask_x[i] = true;
        }


        for(i=0; i<ports_g; i++){

            if(latch_en_x[i] == false){
                ram_en_x = false;
                selected_port = i;

                selected_port_mask_x[i] = false;

                //cout << "selected_port " << pointer << "\n";

                //pointer = (pointer + 1)%ports_g;

                break;
            }
            //pointer = (pointer + 1)%ports_g;


        }
    }



    void regs(){
        int i;
        if(rst_n == false){
            for(i=0; i<ports_g; i++){

                wait_rq_r[i] = false;
                selected_port_mask_x_r[i] = true;
            }
        }
        else if(clk.posedge()){

            for(i=0; i<ports_g; i++){
                wait_rq_r[i] = wait_rq_r_in[i];
                selected_port_mask_x_r[i] = selected_port_mask_x[i];
            }
        }

    }

    void input_latch_seq(){
        int i;
        if(rst_n == false){
            for(i=0; i<ports_g; i++){

                latch_en_x_r[i] = true;
                latch_wr_x_r[i] = true;
                latch_d_r[i] = 0;
                latch_bit_wr_x_r[i] = -1;
                latch_addr_r[i] = 0;
            }
        }

        else if(clk.posedge()){
            for(i=0; i<ports_g; i++){

                //cout << " wait_rq_r_in " << wait_rq_r_in[i] << " : wait_rq_r " <<  wait_rq_r[i] << "\n";
                if(wait_rq_r_in[i]  == true  && wait_rq_r[i] == false){
                    //cout << "hello\n";
                    latch_en_x_r[i] = en_x[i].read();
                    latch_wr_x_r[i] = wr_x[i].read();

                    latch_d_r[i] = d[i].read();
                    latch_bit_wr_x_r[i] = bit_wr_x[i].read();
                    latch_addr_r[i] = addr[i].read();

                }
            }
        }
    }

    void input_latch_comb(){
        int i;
        for(i=0; i<ports_g; i++){

            if(wait_rq_r[i] ==  true){

                latch_en_x[i] = latch_en_x_r[i];
                latch_wr_x[i] = latch_wr_x_r[i];

                latch_d[i] = latch_d_r[i];

                latch_bit_wr_x[i] = latch_bit_wr_x_r[i];
                latch_addr[i] = latch_addr_r[i];
            }
            else{


                latch_en_x[i] = en_x[i];
                latch_wr_x[i] = wr_x[i];

                latch_d[i] = d[i].read();
                latch_bit_wr_x[i] = bit_wr_x[i].read();
                latch_addr[i] = addr[i].read();
            }

        }

    }

    void output_latch_seq(){
        int i;
        if(rst_n == false){

            for(i=0; i<ports_g; i++){
                q_v_r[i] = 0;
            }
        }
        else if(clk.posedge()){
            for(i=0; i<ports_g; i++){
                if( selected_port_mask_x_r[i] == false){
                    q_v_r[i] = ram_q;
                }
            }
        }
    }

    void output_latch_comb(){
        int i;
        for(i=0; i<ports_g; i++){
            if( selected_port_mask_x_r[i] == false){
                q_v[i] = ram_q;

            }
            else{
                q_v[i] = q_v_r[i];
            }
        }
    }

    void pack(){
        int i;
        for(i=0; i<ports_g; i++){
            q[i].write(q_v[i].read());
        }

    }

    void wires(){
        ram_wr_x =  latch_wr_x[selected_port];
        ram_d = latch_d[selected_port];
        ram_bit_wr_x = latch_bit_wr_x[selected_port];
        ram_addr = latch_addr[selected_port];

        int i;
        for(i=0; i<ports_g; i++){

            //cout << "latch_en_x_ " <<i << " : " << latch_en_x[i].read()<< "\n" ;
            //cout << " selected_port_mask_x_" << i << " : " <<  selected_port_mask_x[i]<< "\n";


            wait_rq_r_in[i].write( (latch_en_x[i] + selected_port_mask_x[i])%2); //XOR
            waitrequest[i] = wait_rq_r[i];

            //cout << " wait_rq_r_in_" << i << " : " << (latch_en_x[i] + selected_port_mask_x[i])%2 << "\n";
        }

    }



    SC_CTOR(tta_mem_arbiter)
    {




        int i;



        cout << "Constructing Memory arbiter " << name() << endl;

        SC_METHOD(wires);

        for(i=0; i<ports_g;i++){
            sensitive << wait_rq_r[i] << latch_en_x[i] << latch_d[i] << latch_bit_wr_x[i] << latch_addr[i] << latch_wr_x[i] << selected_port_mask_x[i] << selected_port;
        }

		SC_METHOD(priority_encoder);
		for(i=0; i<ports_g;i++){
		    sensitive << latch_en_x[i] << clk.pos();
        }

		SC_METHOD(regs);
		sensitive << clk.pos() << rst_n.neg();

		SC_METHOD(input_latch_seq);
		sensitive << clk.pos() << rst_n.neg();

		SC_METHOD(input_latch_comb);
		for(i=0; i<ports_g;i++){
            sensitive << wait_rq_r[i] << latch_en_x_r[i] << latch_d_r[i] << latch_bit_wr_x_r[i] << latch_addr_r[i] << en_x[i] << bit_wr_x[i] << d[i] << addr[i] << wr_x[i] << latch_wr_x_r[i];
        }

        SC_METHOD(output_latch_seq);
        sensitive << clk.pos() << rst_n.neg();

        SC_METHOD(output_latch_comb);
        sensitive  << ram_q;

        for(i=0; i<ports_g;i++){
            sensitive << q_v_r[i] << selected_port_mask_x_r[i];
        }


        SC_METHOD(pack);
        for(i=0; i<ports_g;i++){
            sensitive << q_v[i];
        }


        pointer = 0;
        //RESET
        for(i=0; i<ports_g; i++){

            wait_rq_r[i] = false;
            selected_port_mask_x_r[i] = true;
            latch_en_x_r[i] = true;
            latch_wr_x_r[i] = true;
            latch_d_r[i] = 0;
            latch_bit_wr_x_r[i] = -1;
            latch_addr_r[i] = 0;
            q_v_r[i] = 0;


        }


    }

};

#endif