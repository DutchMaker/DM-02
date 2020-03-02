namespace Emulator
{
    public class ControlLines
    {
        public bool A_load { get; set; }
        public bool A_out { get; set; }
        public bool B_load { get; set; }
        public bool B_out { get; set; }
        public bool C_load { get; set; }
        public bool C_out { get; set; }
        public bool H_load { get; set; }
        public bool H_out { get; set; }
        public bool L_load { get; set; }
        public bool L_out { get; set; }
        public bool ALU_load { get; set; }
        public bool F_load { get; set; }
        public bool F_out { get; set; }
        public bool MAR_H_load { get; set; }
        public bool MAR_L_load { get; set; }
        public bool MEM_load { get; set; }
        public bool MEM_out { get; set; }
        public bool PC_H_load { get; set; }
        public bool PC_L_load { get; set; }
        public bool PC_H_out { get; set; }
        public bool PC_L_out { get; set; }
        public bool STK_H_load { get; set; }
        public bool STK_L_load { get; set; }
        public bool STK_H_out { get; set; }
        public bool STK_L_out { get; set; }
        public bool TSTATE_reset { get; set; }
        public bool CLOCK_halt { get; set; }
        public bool STK_inc { get; set; }
        public bool STK_dec { get; set; }
        public bool PC_inc { get; set; }
        public bool PC_MAR_transfer { get; set; }
        public bool STK_MAR_transfer { get; set; }
        public bool MAR_inc { get; set; }
        public bool FSET_z { get; set; }
        public bool FSET_c { get; set; }
        public bool FCLR_z { get; set; }
        public bool FCLR_c { get; set; }

        public void Tick()
        {
        }
    }
}