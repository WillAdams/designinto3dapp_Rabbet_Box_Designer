//!OpenSCAD

Box_width_X = 300;
Box_depth_Y = 200;
Box_height_Z = 100;
Stock_thickness = 8;
Lid_type = "Hinged"; // ["Hinged", "Sliding", "None"]
Display_part = "All"; // ["All", "Front", "Lid", "Left-side", "Right-side", "Back", "Bottom"]
Preview_in_3D = true;
// slider
Lid_position = 25; // [0:90]
// slider
Spacing = 0.2; // [0:0.1:10]
/* [Hidden] */
Scaling_factor = 1;

$fn = $preview ? 32 : 256;

module previewbox() {
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
    if (Lid_type == "Sliding") {
      translate([0, (-((Lid_position / 100) * Box_depth_Y)), (Box_height_Z - Stock_thickness)]){
        if (Display_part == "All" || Display_part == "Lid") {
          Lid();
        }

      }
    } else if (Lid_type == "Hinged") {
      translate([0, 0, Box_height_Z]){
        mirror([0,0,1]){
          rotate([(-Lid_position), 0, 0]){
            rotate([0, 0, 180]){
              translate([(-Box_width_X), (-Box_depth_Y), 0]){
                Lid();
              }
            }
          }
        }
      }
    }

  }
}

module Back() {
  union(){
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

      if (Lid_type == "Hinged") {
        translate([0, (Box_height_Z - Stock_thickness), 0]){
          cube([Box_width_X, Stock_thickness, Stock_thickness], center=false);
          translate([0, (-(Stock_thickness / 2)), (Stock_thickness / 2)]){
            cube([Box_width_X, Stock_thickness, Stock_thickness], center=false);
          }
        }
      }

    }
    translate([(Stock_thickness / 2), (-(Stock_thickness / 2)), (Stock_thickness / 2)]){
      rotate([0, 90, 0]){
        if (Lid_type == "Hinged") {
          translate([0, (Box_height_Z - Stock_thickness), 0]){
            cylinder(r1=(Stock_thickness / 2), r2=(Stock_thickness / 2), h=(Box_width_X - Stock_thickness), center=false);
          }
        }

      }
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

module Front() {
  union(){
    difference() {
      if (Lid_type == "none") {
        translate([(Stock_thickness / 2), 0, 0]){
          cube([(Box_width_X - Stock_thickness), Box_height_Z, Stock_thickness], center=false);
        }
      } else {
        translate([(Stock_thickness / 2), 0, 0]){
          cube([(Box_width_X - Stock_thickness), (Box_height_Z - Stock_thickness), Stock_thickness], center=false);
        }
      }

      translate([0, (Stock_thickness / 2), (Stock_thickness / 2)]){
        cube([Box_width_X, (Stock_thickness / 2), Stock_thickness], center=false);
      }
      if (Lid_type == "Hinged") {
        translate([0, (Box_height_Z - Stock_thickness * 1.5), (Stock_thickness / 2)]){
          cube([Box_width_X, Box_height_Z, Stock_thickness], center=false);
        }
      }

    }
    translate([(Stock_thickness / 2), (-(Stock_thickness / 2)), (Stock_thickness / 2)]){
      rotate([0, 90, 0]){
        if (Lid_type == "Hinged") {
          translate([0, (Box_height_Z - Stock_thickness), 0]){
            cylinder(r1=(Stock_thickness / 2), r2=(Stock_thickness / 2), h=(Box_width_X - Stock_thickness), center=false);
          }
        }

      }
    }
  }
}

module Right_side() {
  difference() {
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

      if (Lid_type == "Hinged") {
        union(){
          translate([(Box_height_Z - Stock_thickness), 0, 0]){
            cube([Stock_thickness, Box_depth_Y, Stock_thickness], center=false);
          }
          translate([(Box_height_Z - Stock_thickness * 1.5), (Stock_thickness / 2), 0]){
            cube([Stock_thickness, (Box_depth_Y - Stock_thickness), Stock_thickness], center=false);
          }
        }
      }

    }

    if (Lid_type == "Hinged") {
      union(){
        translate([(Box_height_Z - Stock_thickness * 1.5), (Stock_thickness / 2), (Stock_thickness / 2)]){
          cylinder(r1=(Stock_thickness / 2), r2=(Stock_thickness / 2), h=Stock_thickness, center=false);
        }
        translate([(Box_height_Z - Stock_thickness * 1.5), (Box_depth_Y - Stock_thickness / 2), (Stock_thickness / 2)]){
          cylinder(r1=(Stock_thickness / 2), r2=(Stock_thickness / 2), h=Stock_thickness, center=false);
        }
      }
    }

  }
}

module Left_side() {
  difference() {
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
      if (Lid_type == "Hinged") {
        union(){
          cube([Stock_thickness, Box_depth_Y, Stock_thickness], center=false);
          translate([(Stock_thickness / 2), (Stock_thickness / 2), 0]){
            cube([Stock_thickness, (Box_depth_Y - Stock_thickness), Stock_thickness], center=false);
          }
        }
      }

    }

    if (Lid_type == "Hinged") {
      union(){
        translate([(Stock_thickness * 1.5), (Stock_thickness / 2), (Stock_thickness / 2)]){
          cylinder(r1=(Stock_thickness / 2), r2=(Stock_thickness / 2), h=Stock_thickness, center=false);
        }
        translate([(Stock_thickness * 1.5), (Box_depth_Y - Stock_thickness / 2), (Stock_thickness / 2)]){
          cylinder(r1=(Stock_thickness / 2), r2=(Stock_thickness / 2), h=Stock_thickness, center=false);
        }
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
  } else if (Lid_type == "Hinged") {
    difference() {
      translate([Stock_thickness, 0, 0]){
        cube([(Box_width_X - Stock_thickness * 2), Box_depth_Y, (Stock_thickness / 2)], center=false);
        translate([0, 0, 0]){
          cube([(Box_width_X - Stock_thickness * 2), (Box_depth_Y - Stock_thickness / 2), Stock_thickness], center=false);
        }
        translate([0, (-(Stock_thickness / 2)), (Stock_thickness / 2)]){
          rotate([0, 90, 0]){
            if (Lid_type == "Hinged") {
              translate([0, Box_depth_Y, 0]){
                cylinder(r1=(Stock_thickness / 2), r2=(Stock_thickness / 2), h=(Box_width_X - Stock_thickness * 2), center=false);
              }
            }

          }
        }
      }

      translate([(Box_width_X / 2), 0, Stock_thickness]){
        sphere(r=(Stock_thickness / 2));
      }
    }
  }

}


translate([(-((Scaling_factor / 2) * Box_width_X)), (-((Scaling_factor / 2) * Box_width_X)), 0]){
  scale([Scaling_factor, Scaling_factor, Scaling_factor]){
    if (Preview_in_3D == true) {
      if (Lid_type == "Hinged") {
        translate([0, Box_depth_Y, 0]){
          mirror([0,1,0]){
            previewbox();
          }
        }
      } else {
        previewbox();
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
