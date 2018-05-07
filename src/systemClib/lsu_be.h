/*
 * lsu.h
 *
 *  SystemC simultion model for TTA BIGENDIAN LSU
 *
 *  Supported instructions:
 *                           LDW - load 32 bit data
 *                           LDH - load signed 16b data
 *                           LDHU  - load unsigned 16b data
 *                           LDQ - load signed 8b data
 *                           LDQU - load unsigned 8b data
 *
 *                           STW - store 32b data
 *                           STH - store 16b data
 *                           STQ - store 8b data
 *
 *
 *  Created on: 01.02.2017
 *      Author: Ilkka Hautala
 *              Center for Machine Vision and Signal Analysis  (CMVS)
 *              University of Oulu
 *              Finland
 */

#ifndef LSU_BE_H_
#define LSU_BE_H_


#include <systemc.h>
#include "tce_systemc.hh"

#define SIGN_EXTEND(VALUE, WIDTH) \
    ((int)(VALUE << (sizeof(SIntWord)*8-(WIDTH))) >> (sizeof(SIntWord)*8-(WIDTH)))

#define ZERO_EXTEND(VALUE, WIDTH) \
    ((VALUE << (sizeof(SIntWord)*8-(WIDTH))) >> (sizeof(SIntWord)*8-(WIDTH)))

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


template<int addrw = 8>
TCE_SC_OPERATION_SIMULATOR(lsu_be){


    sc_out<sc_bv<32/8> > bit_wr_x;
    sc_out<bool> en_x;
    sc_out<bool> wr_x;
    sc_out<sc_bv<addrw> > addr;
    sc_out<sc_bv<32> > d;

    sc_in<sc_bv<32> > q;


	unsigned int addrpipeline[3];

	TCE_SC_OPERATION_SIMULATOR_CTOR(lsu_be){

	    cout << "LSU construction\n";
	}

	TCE_SC_SIMULATE_CYCLE_START{
		wr_x.write(true);
		en_x.write(true);
		bit_wr_x.write("0000");
	}

	TCE_SC_SIMULATE_STAGE{

		addrpipeline[2]=addrpipeline[1];
		addrpipeline[1]=addrpipeline[0];

		if(TCE_SC_OPSTAGE == 0){

		     addr.write(0);
		     en_x.write(true);
		     wr_x.write(true);
		     bit_wr_x.write("0000");


		    if(TCE_SC_OPNAME.compare("LDH") == 0){

		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);
		        en_x.write(false);
		        wr_x.write(true);
		        addrpipeline[0] = TCE_SC_UINT(1);

		    }
		    else if(TCE_SC_OPNAME.compare("LDHU") == 0){
		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);
		        en_x.write(false);
		        wr_x.write(true);
		        addrpipeline[0] = TCE_SC_UINT(1);
		    }
		    else if(TCE_SC_OPNAME.compare("LDQ") == 0){
		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);
		        en_x.write(false);
		        wr_x.write(true);
		        addrpipeline[0] = TCE_SC_UINT(1);
		    }

		    else if(TCE_SC_OPNAME.compare("LDQU") == 0){
		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);
		        en_x.write(false);
		        wr_x.write(true);
		        addrpipeline[0] = TCE_SC_UINT(1);

		    }

		    else if(TCE_SC_OPNAME.compare("LDW") == 0){
		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);
		        en_x.write(false);
		        wr_x.write(true);
		        addrpipeline[0] = TCE_SC_UINT(1);
		    }

		    else if(TCE_SC_OPNAME.compare("LSEP8") == 0){
		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);
		        en_x.write(false);
		        wr_x.write(true);
		        addrpipeline[0] = TCE_SC_UINT(1);
		    }

		    else if(TCE_SC_OPNAME.compare("STH") == 0){

		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);
		        en_x.write(false);
		        wr_x.write(false);

                //cout << "stq\n";

		        unsigned int bytemask = TCE_SC_UINT(1) & 0x00000003;

		        sc_bv<32/8> bytemask_bv;

		        if(bytemask == 0){
		            d.write(TCE_SC_INT(2));
		            bytemask_bv = "0011";
		            bit_wr_x.write(bytemask_bv);
		        }
		        else if(bytemask == 2){
		            d.write(TCE_SC_INT(2)<<16);
		            bytemask_bv = "1100";
		            bit_wr_x.write(bytemask_bv);
		        }
		        else{
		            cout << "[ERROR] STH operation addr: " << TCE_SC_UINT(1) << '\n';
		        }


		    }

		    else if(TCE_SC_OPNAME.compare("STQ") == 0){

		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);

		        en_x.write(false);
		        wr_x.write(false);

                //cout << "stq\n";

		        unsigned int bytemask = TCE_SC_UINT(1) & 0x00000003;
		        sc_bv<32/8> bytemask_bv;

		        if(bytemask == 0){
		            d.write(TCE_SC_UINT(2));
		            bytemask_bv = "0001";
		            bit_wr_x.write(bytemask_bv);
		        }
		        else if(bytemask == 1){
		            d.write(TCE_SC_UINT(2)<<8);
		            bytemask_bv = "0010";
		            bit_wr_x.write(bytemask_bv);
		        }
		        else if(bytemask == 2){
		            d.write(TCE_SC_UINT(2)<<16);
		            bytemask_bv = "0100";
		            bit_wr_x.write(bytemask_bv);
		        }
		        else if(bytemask == 3){
		            d.write(TCE_SC_UINT(2)<<24);
		            bytemask_bv = "1000";
		            bit_wr_x.write(bytemask_bv);
		        }
		        else{
		            cout << "[ERROR] STQ operation addr: " << TCE_SC_UINT(1) << '\n';
		        }
		    }

		    else if(TCE_SC_OPNAME.compare("STW") == 0){

		        sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);

		        en_x.write(false);
		        wr_x.write(false);


		        unsigned int bytemask = TCE_SC_UINT(1) & 0x00000003;
		        sc_bv<32/8> bytemask_bv;

                cout << "LSUBE STW -- Address " << addrpipeline[2] <<  "\tdata" << (TCE_SC_UINT(2) & 0x000000ff) << "-";
                cout << ((TCE_SC_UINT(2) & 0x0000ff00) >> 8) << "-";
                cout << ((TCE_SC_UINT(2) & 0x00ff0000) >> 16) << "-";
                cout << ((TCE_SC_UINT(2) & 0xff000000) >> 24) << "\n";

                if(bytemask == 0){
                    sc_bv<32/8> bytemask_bv;
                    bytemask_bv = "1111";
                    bit_wr_x.write(bytemask_bv);
                    d = (TCE_SC_UINT(2));

                }
                else{
                    cout << "[ERROR] unaligned STW operation addr: " << TCE_SC_UINT(1) << '\n';
                }

		    }

		    else if(TCE_SC_OPNAME.compare("SJOIN8") == 0){

                sc_bv<addrw> addr_temp;
		        addr_temp = TCE_SC_UINT(1)>>2;
		        addr.write(addr_temp);

		        en_x.write(false);
		        wr_x.write(false);

		        int data1, data2, data3, data4;
				data1 =  TCE_SC_INT(2)  & 0x000000ff;
				data2 = (TCE_SC_INT(3)<<8)  & 0x0000ff00;
				data3 = (TCE_SC_INT(4)<<16) & 0x00ff0000;
				data4 = (TCE_SC_INT(5)<<24) & 0xff000000;

                d.write(data1 | data2 | data3 | data4);

		        unsigned int bytemask = TCE_SC_UINT(1) & 0x00000003;
		        sc_bv<32/8> bytemask_bv;

                if(bytemask == 0){
                    sc_bv<32/8> bytemask_bv;
                    bytemask_bv = "1111";
                    bit_wr_x.write(bytemask_bv);
                }
                else{
                    cout << "[ERROR] unaligned STW operation addr: " << TCE_SC_UINT(1) << '\n';
                }

		    }

		    else{
		        cout << "[ERROR] LSU simulation model has no support for operation " << TCE_SC_OPNAME << '\n';
		        return false;
		    }

			return true;
		}

		if(TCE_SC_OPSTAGE== 1){


		}

		if(TCE_SC_OPSTAGE== 2){




		    if(TCE_SC_OPNAME.compare("LDQU")==0){

				unsigned int bytemask = addrpipeline[2] & 0x00000003;
				sc_bv<32> q_bv;
                q_bv = q.read();

                //cout << "LDQU " << q.read() << "\n";

 
				if(bytemask == 0){
				    //debugfile << "LDQU " << addrpipeline[2] <<  "\tdata " << (q_bv.to_uint() & 0x000000ff) << "\t@ "<< sc_time_stamp() <<"\n";
                    TCE_SC_OUTPUT(2) = (q_bv.to_uint() & 0x000000ff);
				}
				else if (bytemask == 1){
				    //debugfile << "LDQU " << addrpipeline[2] <<  "\tdata " << ((q_bv.to_uint() & 0x0000ff00) >> 8) << "\t@ "<< sc_time_stamp() <<"\n";
                    TCE_SC_OUTPUT(2) = ((q_bv.to_uint() & 0x0000ff00) >> 8);
				}
				else if (bytemask == 2){
				    //debugfile << "LDQU " << addrpipeline[2] <<  "\tdata " << ((q_bv.to_uint() & 0x00ff0000) >> 16) << "\t@ "<< sc_time_stamp() <<"\n";
                    TCE_SC_OUTPUT(2) = ((q_bv.to_uint() & 0x00ff0000) >> 16);
				}
				else if (bytemask == 3){
				    //debugfile << "LDQU " << addrpipeline[2] <<  "\tdata " << ((q_bv.to_uint() & 0xff000000) >> 24) << "\t@ "<< sc_time_stamp() <<"\n";
                    TCE_SC_OUTPUT(2) = ((q_bv.to_uint() & 0xff000000) >> 24);
				}
				else{
                    cout << "[ERROR] Misaligment LDQU operation addr: " << TCE_SC_UINT(1) << '\n';
				}



			}
			else if(TCE_SC_OPNAME.compare("LDQ")==0){

				unsigned int bytemask = addrpipeline[2] & 0x00000003;
				sc_bv<32> q_bv;
                q_bv = q.read();
                //cout << "LDQ OUTPUT" << q.read() << "\n";

				if(bytemask == 0){
                    TCE_SC_OUTPUT(2) = SIGN_EXTEND(q_bv.to_uint() & 0x000000ff,32);
				}
				else if (bytemask == 1){
                    TCE_SC_OUTPUT(2) = SIGN_EXTEND((q_bv.to_uint() & 0x0000ff00) >> 8,32);
				}
				else if (bytemask == 2){
                    TCE_SC_OUTPUT(2) = SIGN_EXTEND((q_bv.to_uint() & 0x00ff0000) >> 16,32);
				}
				else if (bytemask == 3 ){
                   TCE_SC_OUTPUT(2) = SIGN_EXTEND((q_bv.to_uint() & 0xff000000) >> 24,32);
				}
				else{
                    cout << "[ERROR] Misaligment LDQ operation addr: " << TCE_SC_UINT(1) << '\n';
				}

			}
			else if(TCE_SC_OPNAME.compare("LDHU")==0){

				unsigned int bytemask = addrpipeline[2] & 0x00000003;
				sc_bv<32> q_bv;
                q_bv = q.read();

                //cout << "LDHU OUTPUT" << q.read() << "\n";

				if(bytemask == 0){
                    TCE_SC_OUTPUT(2) = (q_bv.to_uint() & 0x0000ffff);
				}
				else if (bytemask == 2){
                    TCE_SC_OUTPUT(2) = (q_bv.to_uint() & 0xffff0000) >> 16;
				}
				else{
                    cout << "[ERROR] Misaligment LDHU operation addr: " << TCE_SC_UINT(1) << '\n';
				}

			}

			else if(TCE_SC_OPNAME.compare("LDH")==0){
				unsigned int bytemask = addrpipeline[2] & 0x00000003;
				sc_bv<32> q_bv;
                q_bv = q.read();
                //cout << "LDH OUTPUT" << q.read() << "\n";

				if(bytemask == 0){
                    TCE_SC_OUTPUT(2) = SIGN_EXTEND(q_bv.to_uint() & 0x0000ffff,32);
				}
				else if (bytemask == 2){
                    TCE_SC_OUTPUT(2) = SIGN_EXTEND((q_bv.to_uint() & 0xffff0000) >> 16,32);
				}
				else{
                    cout << "[ERROR] Misaligment LDH operation addr: " << TCE_SC_UINT(1) << '\n';
				}
			}
			else if(TCE_SC_OPNAME.compare("LDW")==0){

			    unsigned int bytemask = addrpipeline[2] & 0x00000003;
				sc_bv<32> q_bv;
				q_bv = q.read();

				cout << "LSUBE -- Address " << addrpipeline[2] <<  "\tdata in " << (q_bv.to_uint() & 0x000000ff) << "-";
                cout << ((q_bv.to_uint() & 0x0000ff00) >> 8) << "-";
                cout << ((q_bv.to_uint() & 0x00ff0000) >> 16) << "-";
                cout << ((q_bv.to_uint() & 0xff000000) >> 24) << "\t";


                if(bytemask == 0){
                    cout << "LDW OUTPUT " << (q_bv.to_int()) << "\n";
                    TCE_SC_OUTPUT(2) = (q_bv.to_uint());
                }
                else{
                    cout << "[ERROR] Misaligment LDW operation addr: " << TCE_SC_UINT(1) << '\n';
                }
			}
			else if(TCE_SC_OPNAME.compare("LSEP8")==0){

			    //unsigned int bytemask = addrpipeline[2] & 0x00000003;
				sc_bv<32> q_bv;
				//
                q_bv = q.read();
                //if(bytemask == 0){
                    TCE_SC_OUTPUT(2) =  0x000000ff & q_bv.to_int();
                    TCE_SC_OUTPUT(3) = (0x0000ff00 & q_bv.to_int())>>8;
                    TCE_SC_OUTPUT(4) = (0x00ff0000 & q_bv.to_int())>>16;
                    TCE_SC_OUTPUT(5) = (0xff000000 & q_bv.to_int())>>24;
                //}
                //else{
                //    cout << "[ERROR] Misaligment LSEP8 operation addr: " << addrpipeline[2] << '\n';
                //}
			}
            else{
                cout << "[ERROR] LSU simulation model has no support for operation " << TCE_SC_OPNAME << '\n';
            }

			return true;
		}
		else{
			return false;
		}

	}

};


#endif