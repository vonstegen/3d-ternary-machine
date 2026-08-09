// BT-IS core: minimal synthesizable Verilog.
//
// This is a *behavioral* model suitable for FPGA synthesis (the
// `cube` rotations and arithmetic are O(1) LUT lookups; the rest is
// standard sequential logic). It is not a high-performance design
// — the goal is to demonstrate that the architecture can be
// synthesized at all and to estimate area / latency / power.
//
// Targets: any 7-series Xilinx or Cyclone-series Intel FPGA.
// BRAM is used for the 27-state LUTs; the cube registers fit
// comfortably in flip-flops.
//
// Status: behavioral model.  Synthesis + area / latency numbers
// require yosys + nextpnr for an iCE40 target, or Vivado for a
// Xilinx target.  This is Stage D's planned follow-up.

module btis_core (
    input  wire        clk,
    input  wire        rst_n,

    input  wire [7:0]  instr_opcode,   // from instruction memory
    input  wire [7:0]  instr_arg,      // signed: -128..127
    input  wire [15:0] instr_target,   // branch target (instruction index)

    output reg  [4:0]  C,              // 5-bit cube index (0..26)
    output reg  [4:0]  F,              // flag cube (5-bit index)
    output reg  [31:0] steps,          // total steps executed
    output reg         halted
);

    // 27-state rotation/reflection LUTs.  Each is 27 entries of
    // 5-bit indices.  In hardware these become 27x5 = 135 bits per
    // table, packed into a single BRAM (or 5 BRAMs of 27x1).
    reg [4:0] rot_z_90  [0:26];
    reg [4:0] rot_z_180 [0:26];
    reg [4:0] rot_z_270 [0:26];
    reg [4:0] rot_x_90  [0:26];
    reg [4:0] rot_x_180 [0:26];
    reg [4:0] rot_x_270 [0:26];
    reg [4:0] rot_y_90  [0:26];
    reg [4:0] rot_y_180 [0:26];
    reg [4:0] rot_y_270 [0:26];
    reg [4:0] neg       [0:26];
    reg [4:0] refl_x    [0:26];
    reg [4:0] refl_y    [0:26];
    reg [4:0] refl_z    [0:26];

    initial begin
        // Filled at synthesis time by a generator; for simulation,
        // we hardcode a representative table.
        rot_z_90 [0]  = 5'd0;  rot_z_90 [1]  = 5'd6;
        rot_z_90 [2]  = 5'd3;  rot_z_90 [3]  = 5'd8;
        rot_z_90 [4]  = 5'd1;  rot_z_90 [5]  = 5'd7;
        rot_z_90 [6]  = 5'd2;  rot_z_90 [7]  = 5'd4;
        rot_z_90 [8]  = 5'd9;  rot_z_90 [9]  = 5'd15;
        rot_z_90 [10] = 5'd12; rot_z_90 [11] = 5'd17;
        rot_z_90 [12] = 5'd10; rot_z_90 [13] = 5'd16;
        rot_z_90 [14] = 5'd11; rot_z_90 [15] = 5'd13;
        rot_z_90 [16] = 5'd18; rot_z_90 [17] = 5'd24;
        rot_z_90 [18] = 5'd21; rot_z_90 [19] = 5'd26;
        rot_z_90 [20] = 5'd19; rot_z_90 [21] = 5'd25;
        rot_z_90 [22] = 5'd20; rot_z_90 [23] = 5'd22;
        rot_z_90 [24] = 5'd23; rot_z_90 [25] = 5'd14;
        rot_z_90 [26] = 5'd26; // placeholder; real table filled by gen
    end

    // Cube arithmetic: cube_add.  Implemented combinatorially.
    function [4:0] cube_add;
        input [4:0] a, b;
        reg signed [3:0] sx, sy, sz;
        reg signed [3:0] cx, cy, cz;
        reg signed [1:0] dx, dy, dz;
        begin
            sx = a[1:0] - 1 + b[1:0] - 1; // (a.x + b.x), x in {-1,0,+1}
            sy = a[3:2] - 1 + b[3:2] - 1;
            sz = a[4]   ? 2 : (a[3:2] == 2 ? 1 : 0);
            // (Simplified; full impl handles all carries.)
            dx = (sx > 1) ? 1 : (sx < -1 ? -1 : sx);
            cx = (sx > 1) ? (sx - 3) : (sx < -1 ? (sx + 3) : 0);
            dy = (sy + cx > 1) ? 1 : (sy + cx < -1 ? -1 : sy + cx);
            cy = (sy + cx > 1) ? (sy + cx - 3) : (sy + cx < -1 ? (sy + cx + 3) : 0);
            dz = (sz + cy > 1) ? 1 : (sz + cy < -1 ? -1 : sz + cy);
            cube_add = {dz[0], dy[1:0] + 2, dx[1:0] + 2};
        end
    endfunction

    // Opcode constants (matching src/isa.rs).
    localparam OP_NOP     = 8'd0;
    localparam OP_HALT    = 8'd192;
    localparam OP_LOADC   = 8'd1;
    localparam OP_ROT_Z_90  = 8'd32;
    localparam OP_ROT_Z_180 = 8'd33;
    localparam OP_ROT_Z_270 = 8'd34;
    localparam OP_ROT_X_90  = 8'd35;
    localparam OP_ROT_X_180 = 8'd36;
    localparam OP_ROT_X_270 = 8'd37;
    localparam OP_ROT_Y_90  = 8'd38;
    localparam OP_ROT_Y_180 = 8'd39;
    localparam OP_ROT_Y_270 = 8'd40;
    localparam OP_REFLECT_X = 8'd56;
    localparam OP_REFLECT_Y = 8'd57;
    localparam OP_REFLECT_Z = 8'd58;
    localparam OP_NEG       = 8'd59;
    localparam OP_IADD      = 8'd64;
    localparam OP_ISUB      = 8'd65;
    localparam OP_CUBE_ADD  = 8'd70;
    localparam OP_CMP       = 8'd96;
    localparam OP_BR_NEG    = 8'd97;
    localparam OP_BR_ZERO   = 8'd98;
    localparam OP_BR_POS    = 8'd99;
    localparam OP_JMP       = 8'd100;
    localparam OP_OUTI      = 8'd3;
    localparam OP_OUTV      = 8'd4;

    reg [4:0] next_C;
    reg [4:0] next_F;
    reg       next_halted;
    reg [4:0] br_target;  // resolved branch target (instruction index)

    always @(*) begin
        next_C = C;
        next_F = F;
        next_halted = halted;
        br_target = instr_target[4:0];

        case (instr_opcode)
            OP_NOP: ;
            OP_HALT: next_halted = 1'b1;
            OP_LOADC: next_C = {instr_arg[1:0], 3'b0} + 5'd13; // (a,a,a) -> idx
            OP_ROT_Z_90:  next_C = rot_z_90[C];
            OP_ROT_Z_180: next_C = rot_z_180[C];
            OP_ROT_Z_270: next_C = rot_z_270[C];
            OP_ROT_X_90:  next_C = rot_x_90[C];
            OP_ROT_X_180: next_C = rot_x_180[C];
            OP_ROT_X_270: next_C = rot_x_270[C];
            OP_ROT_Y_90:  next_C = rot_y_90[C];
            OP_ROT_Y_180: next_C = rot_y_180[C];
            OP_ROT_Y_270: next_C = rot_y_270[C];
            OP_REFLECT_X: next_C = refl_x[C];
            OP_REFLECT_Y: next_C = refl_y[C];
            OP_REFLECT_Z: next_C = refl_z[C];
            OP_NEG:       next_C = neg[C];
            OP_CUBE_ADD:  next_C = cube_add(C, F); // placeholder: needs mem read
            OP_IADD: ; // TODO
            OP_ISUB: ; // TODO
            OP_CMP: ; // TODO: set F based on sign of C.x - arg
            OP_BR_NEG: ;
            OP_BR_ZERO: ;
            OP_BR_POS: ;
            OP_JMP: ;
            default: ;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            C <= 5'd13;
            F <= 5'd13;
            steps <= 32'd0;
            halted <= 1'b0;
        end else begin
            C <= next_C;
            F <= next_F;
            steps <= steps + 1;
            halted <= next_halted;
        end
    end

endmodule
