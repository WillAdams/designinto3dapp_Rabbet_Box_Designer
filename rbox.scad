//!OpenSCAD

Box_width_X = 300;
Box_depth_Y = 200;
Box_height_Z = 100;
Stock_thickness = 8;
Lid_type = "None"; // ["None", "Sliding"]
Display_part = "All"; // ["Bottom", "Front", "Left-side", "Right-side", "Back", "Lid"]
Preview_in_3D = true;

/* [Hidden] */
Lid_position = 0;
Spacing = 2;


Scaling_factor = 0.1;
item = 0;

module Back() {
  difference() {
    translate([(Stock_thickness / 2), 0, 0]){
      cube([(Box_width_X - Stock_thickness), Box_height_Z, Stock_thickness], center=false);
    }

    translate([0, (Stock_thickness / 2), (Stock_thickness / 2)]){
      cube([Box_width_X, (Stock_thickness / 2), Stock_thickness], center=false);
    }
    if (Lid_type == "Sliding") {
      translate([0, (Box_height_Z - Stock_thickness), (Stock_thickness / 2)]){
        cube([Box_width_X, (Stock_thickness / 2), Stock_thickness], center=false);
      }
    }

  }
}

module Front() {
  difference() {
    if (Lid_type == "Sliding") {
      translate([(Stock_thickness / 2), 0, 0]){
        cube([(Box_width_X - Stock_thickness), (Box_height_Z - Stock_thickness), Stock_thickness], center=false);
      }
    } else {
      translate([(Stock_thickness / 2), 0, 0]){
        cube([(Box_width_X - Stock_thickness), Box_height_Z, Stock_thickness], center=false);
      }
    }

    translate([0, (Stock_thickness / 2), (Stock_thickness / 2)]){
      cube([Box_width_X, (Stock_thickness / 2), Stock_thickness], center=false);
    }
  }
}

module Bottom() {
  translate([(Stock_thickness / 2), (Stock_thickness / 2), 0]){
    union(){
      cube([(Box_width_X - Stock_thickness), (Box_depth_Y - Stock_thickness), (Stock_thickness / 2)], center=false);
      translate([(Stock_thickness / 2), (Stock_thickness / 2), 0]){
        cube([(Box_width_X - Stock_thickness * 2), (Box_depth_Y - Stock_thickness * 2), Stock_thickness], center=false);
      }
    }
  }
}

module Left_side() {
  union(){
    cube([Box_height_Z, Box_depth_Y, (Stock_thickness / 2)], center=false);
    if (Lid_type == "Sliding") {
      cube([(Stock_thickness / 2), (Box_depth_Y - Stock_thickness), Stock_thickness], center=false);
    }

    if (Lid_type == "Sliding") {
      translate([Stock_thickness, Stock_thickness, 0]){
        cube([(Box_height_Z - Stock_thickness * 2), (Box_depth_Y - Stock_thickness * 2), Stock_thickness], center=false);
      }
    } else {
      translate([0, Stock_thickness, 0]){
        cube([(Box_height_Z - Stock_thickness), (Box_depth_Y - Stock_thickness * 2), Stock_thickness], center=false);
      }
    }

    translate([(Box_height_Z - Stock_thickness / 2), Stock_thickness, 0]){
      cube([(Stock_thickness / 2), (Box_depth_Y - Stock_thickness * 2), Stock_thickness], center=false);
    }
  }
}

module Right_side() {
  union(){
    cube([Box_height_Z, Box_depth_Y, (Stock_thickness / 2)], center=false);
    translate([0, Stock_thickness, 0]){
      cube([(Stock_thickness / 2), (Box_depth_Y - Stock_thickness * 2), Stock_thickness], center=false);
    }
    translate([Stock_thickness, Stock_thickness, 0]){
      if (Lid_type == "Sliding") {
        cube([(Box_height_Z - Stock_thickness * 2), (Box_depth_Y - Stock_thickness * 2), Stock_thickness], center=false);
      } else {
        cube([(Box_height_Z - Stock_thickness), (Box_depth_Y - Stock_thickness * 2), Stock_thickness], center=false);
      }

    }
    if (Lid_type == "Sliding") {
      translate([(Box_height_Z - Stock_thickness / 2), 0, 0]){
        cube([(Stock_thickness / 2), (Box_depth_Y - Stock_thickness), Stock_thickness], center=false);
      }
    }

  }
}

module Lid() {
  if (Lid_type == "Sliding") {
    translate([(Stock_thickness / 2), 0, 0]){
      union(){
        cube([(Box_width_X - Stock_thickness), (Box_depth_Y - Stock_thickness / 2), (Stock_thickness / 2)], center=false);
        translate([(Stock_thickness / 2), 0, 0]){
          cube([(Box_width_X - Stock_thickness * 2), (Box_depth_Y - Stock_thickness), Stock_thickness], center=false);
        }
      }
    }
  }

}

translate([(-((Scaling_factor / 2) * Box_width_X)), (-((Scaling_factor / 2) * Box_width_X)), 0]){
  scale([Scaling_factor, Scaling_factor, Scaling_factor]){
    if (Preview_in_3D == true) {
      union(){
        translate([0, 0, Stock_thickness]){
          mirror([0,0,1]){
            if (Display_part == "All" || Display_part == "Bottom") {
              Bottom();
            }

          }
        }
        rotate([90, 0, 0]){
          mirror([0,0,1]){
            translate([0, 0, (-Spacing)]){
              if (Display_part == "All" || Display_part == "Front") {
                Front();
              }

            }
          }
        }
        translate([(-Spacing), 0, Box_height_Z]){
          rotate([0, 90, 0]){
            if (Display_part == "All" || Display_part == "Left-side") {
              Left_side();
            }

          }
        }
        translate([(Box_width_X + Spacing), 0, 0]){
          rotate([0, 270, 0]){
            if (Display_part == "All" || Display_part == "Right-side") {
              Right_side();
            }

          }
        }
        translate([0, (Box_depth_Y + Spacing), 0]){
          rotate([90, 0, 0]){
            if (Display_part == "All" || Display_part == "Back") {
              Back();
            }

          }
        }
        translate([0, (-((Lid_position / 100) * Box_depth_Y)), (Box_height_Z - Stock_thickness)]){
          if (Display_part == "All" || Display_part == "Lid") {
            Lid();
          }

        }
      }
    } else {
      union(){
        if (Display_part == "All") {
          translate([30, 30, 0]){
            Bottom();
          }
        } else if (Display_part == "Bottom") {
          Bottom();
        }

        if (Display_part == "All") {
          translate([30, (Box_depth_Y + 114), 0]){
            Front();
          }
        } else if (Display_part == "Front") {
          Front();
        }

        if (Display_part == "All") {
          translate([30, ((Box_depth_Y + Box_height_Z) + 171), 0]){
            Left_side();
          }
        } else if (Display_part == "Left-side") {
          Left_side();
        }

        if (Display_part == "All") {
          translate([(Box_width_X + 90), ((Box_depth_Y + Box_height_Z) + 171), 0]){
            Right_side();
          }
        } else if (Display_part == "Right-side") {
          Right_side();
        }

        if (Display_part == "All") {
          translate([(Box_width_X + 90), (Box_depth_Y + 114), 0]){
            Back();
          }
        } else if (Display_part == "Back") {
          Back();
        }

        if (Display_part == "All") {
          translate([(Box_width_X + 90), 30, 0]){
            Lid();
          }
        } else if (Display_part == "Lid") {
          Lid();
        }

      }
    }

  }
}