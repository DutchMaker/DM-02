// Conservative interval models, not transistor-level device qualification.
module pc161 #(parameter real TQ=0,TTC=0,TDSU=15,TDH=5,TESU=20,TEH=3,TLSU=18,TLH=3,TR=22,TRESET=30,TLOW=24)
 (input [3:0] d,input clk,reset_n,load_n,cep,cet,output [3:0] q,output tc);
 reg [3:0] stored;
 real ld=-10000,le=-10000,ll=-10000,lc=-10000,lr=-10000,lf=-10000,la=-10000;
 reg armed=0;
 assign #(TQ) q=stored;
 assign #(TTC) tc=cet && (&stored);
 always @(d) begin
   if(armed && reset_n && !load_n && $realtime-lc<TDH) $fatal(1,"PC data hold %m");
   ld=$realtime;
 end
 always @(cep or cet) begin
   if(armed && reset_n && $realtime-lc<TEH) $fatal(1,"PC enable hold %m");
   le=$realtime;
 end
 always @(load_n) begin
   if(armed && reset_n && $realtime-lc<TLH) $fatal(1,"PC load hold %m");
   ll=$realtime;
 end
 always @(negedge clk) lf=$realtime;
 always @(negedge reset_n) la=$realtime;
 always @(posedge reset_n) begin
   if(armed && $realtime-la<TRESET) $fatal(1,"PC reset pulse %m");
   lr=$realtime;
 end
 always @(posedge clk or negedge reset_n) begin
   if(!reset_n) begin stored<=0;armed=1;end
   else begin
     if(armed) begin
       if($realtime-lr<TR) $fatal(1,"PC reset recovery %m");
       if($realtime-lf<TLOW) $fatal(1,"PC clock low pulse %m");
       if($realtime-ll<TLSU) $fatal(1,"PC load setup %m");
       if(!load_n && $realtime-ld<TDSU) $fatal(1,"PC data setup %m");
       if(load_n && $realtime-le<TESU) $fatal(1,"PC enable setup %m");
     end
     if(!load_n) stored<=d;
     else if(cep && cet) stored<=stored+1'b1;
     lc=$realtime;
   end
 end
endmodule

module pc175 #(parameter real TQ=0,TSU=2,TH=2,TR=1)
 (input [3:0] d,input clk,reset_n,output [3:0] q,nq);
 reg [3:0] stored;reg armed=0;
 real ld=-10000,lc=-10000,lr=-10000;
 assign #(TQ) q=stored;assign #(TQ) nq=~stored;
 always @(d) begin
   if(armed && reset_n && $realtime-lc<TH) $fatal(1,"PC carry hold %m");
   ld=$realtime;
 end
 always @(posedge reset_n) lr=$realtime;
 always @(posedge clk or negedge reset_n) begin
   if(!reset_n) begin stored<=0;armed=1;end
   else begin
     if(armed && $realtime-ld<TSU) $fatal(1,"PC carry setup %m");
     if(armed && $realtime-lr<TR) $fatal(1,"PC carry reset recovery %m");
     stored<=d;lc=$realtime;
   end
 end
endmodule
