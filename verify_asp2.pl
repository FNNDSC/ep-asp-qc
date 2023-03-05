#!/usr/bin/env perl

# Plot surfaces and vertex-wise data.
# Modified from verify_clasp.
#
# I wrote this in a hurry. Parallelism and declarativeness would be nice, but ain't got time for that...
#
# N.B.: This script does not care to show good errors nor validate its arguments.
# My recommendation is to write a wrapper for this script, such as verify_surfaces.py
#
# Copyright Alan C. Evans
# Professor of Neurology
# McGill University
#

use strict;
use warnings "all";
use List::Util qw( min max );
use File::Temp qw/ tempdir /;

my ($main_title, $output, @args) = @ARGV;

unless($output) {
  print "USAGE\n\n";
  print "\t$0 title output.png [inputs...]\n\n";
  print "Inputs to this program are 3-tuples indicating surfaces, and 5-tuples of values.\n";
  print "First, specify surfaces as: caption left.obj right.obj\n";
  print "After all surfaces arguments, specify data files: caption left.txt right.txt min max\n";
  print "\n";
  print "EXAMPLES\n\n";
  print "One layer, one dataset:\n\n";
  print "\t$0 \"WM Extraction\" wm_extraction_qc.png  \\\n";
  print "\t\"Marching-cubes white matter surface\" wm_left_81920.obj wm_left_right_81920.obj  \\\n";
  print "\t\"Distance error\" left_disterr.txt right_disterr.txt -3.0 3.0\n";
  print "\n\n";
  print "Inner and outer layers, multiple datasets:\n\n";
  print "\t$0 \"Inner subplate fitting\" spfit_qc.png  \\\n";
  print "\t\"Outer SP\" spouter_left_81920.obj spouter_right_81920.obj      \\\n";
  print "\t\"Inner SP\" spinner_left_81920.obj spinner_right_81920.obj      \\\n";
  print "\t\"Distance error\" left_disterr.txt right_disterr.txt -3.0 3.0   \\\n";
  print "\t\"Smoothness error\" left_smtherr.txt right_smtherr.txt 0.0 2.0  \\\n";
  print "\t\"Tlink thickness\" left_tlink.txt right_tnear.txt 0.0 10.0\n";
  print "\n";
  exit(1);
}

################################################################################
# ARGUMENT PARSING
################################################################################

my @surface_args = ();
my @data_args = ();

my @buffer = ();
my $arg_type = "";

while (my $arg = shift(@args)) {
  my $current_len = scalar @buffer;
  if ($current_len == 1) {
    $arg_type = $arg =~ /.*\.obj/ ? "surface" : "data";
  }
  push @buffer, $arg;
  if ($current_len == 2 && $arg_type eq 'surface') {
    push @surface_args, @buffer;
    @buffer = ();
  } elsif ($current_len == 4 && $arg_type eq 'data') {
    push @data_args, @buffer;
    @buffer = ();
  }
}

if (@buffer) {
  print "Wrong number of arguments.\n";
  exit(1);
}

################################################################################
# GLOBAL VARIABLES
################################################################################

my $tmpdir = tempdir( CLEANUP => 1 );
my $tilesize = 200;
my @mont_args = ();
my @DrawText = ( '-font', 'DejaVu-Sans' );

my $num_rows = 0;
my $xpos = 2*$tilesize;
my $ypos = 15;
my $xpos2 = 3.185*$tilesize;   # position for L/R labels
my $xpos3 = 3.84*$tilesize;
my $xpos4 = 4.185*$tilesize;
my $xpos5 = 4.84*$tilesize;

# draw main title
push( @DrawText, ( '-annotate', "0x0+${xpos}+${ypos}", "$main_title" ) );

################################################################################
# DRAW SURFACES
################################################################################

for ( my $i = 0;  $i < @surface_args;  $i += 3 ) {
  my ($caption_text, $surface_left, $surface_right) = @surface_args[$i .. $i + 2];

  # ROW 1: white left hemi surfaces + white top and bottom views
  $num_rows += 1;
  $ypos += 0.065 * $tilesize;
  push(@DrawText, ('-annotate', "0x0+${xpos2}+${ypos}", "L"));
  push(@DrawText, ('-annotate', "0x0+${xpos3}+${ypos}", "R"));
  push(@DrawText, ('-annotate', "0x0+${xpos4}+${ypos}", "R"));
  push(@DrawText, ('-annotate', "0x0+${xpos5}+${ypos}", "L"));
  $ypos -= 0.065 * $tilesize;
  foreach my $pos ('default', 'left', 'right') {
    make_hemi($surface_left, "${tmpdir}/${num_rows}_hemi_${pos}.rgb", $pos);
    push(@mont_args, "${tmpdir}/${num_rows}_hemi_${pos}.rgb");
  }
  foreach my $pos ('top', 'bottom') {
    make_surface($surface_left, $surface_right, "${tmpdir}/${num_rows}_surf_${pos}.rgb", $pos);
    push(@mont_args, "${tmpdir}/${num_rows}_surf_${pos}.rgb");
  }

  # ROW 2: white right hemi surfaces + white front and back views
  $num_rows += 1;
  $ypos += $tilesize;
  $ypos += 0.045 * $tilesize;
  push(@DrawText, ('-annotate', "0x0+${xpos2}+${ypos}", "R"));
  push(@DrawText, ('-annotate', "0x0+${xpos3}+${ypos}", "L"));
  push(@DrawText, ('-annotate', "0x0+${xpos4}+${ypos}", "L"));
  push(@DrawText, ('-annotate', "0x0+${xpos5}+${ypos}", "R"));
  $ypos -= 0.045 * $tilesize;
  foreach my $pos ('flipped', 'right', 'left') {
    make_hemi($surface_right, "${tmpdir}/${num_rows}_hemi_${pos}.rgb", $pos);
    push(@mont_args, "${tmpdir}/${num_rows}_hemi_${pos}.rgb");
  }
  foreach my $pos ('front', 'back') {
    make_surface($surface_left, $surface_right, "${tmpdir}/${num_rows}_surf_${pos}.rgb", $pos);
    push(@mont_args, "${tmpdir}/${num_rows}_surf_${pos}.rgb");
  }

  push( @DrawText, ( '-annotate', "0x0+${xpos}+${ypos}", "$caption_text" ) );
  # leftover stuff. It used to draw 3 lines of text and move them places...
  $ypos += $tilesize - 0.10*$tilesize;
  $xpos -= 0.2*$tilesize;
  $xpos += 0.2*$tilesize;
  $ypos += 0.10*$tilesize;
  $ypos += 0.10*$tilesize;
  $ypos -= 0.10*$tilesize;
  $ypos += 0.065*$tilesize;
}

################################################################################
# CALCULATE MID SURFACES
################################################################################

my $mid_left = "${tmpdir}/mid_surface_left.obj";
my $mid_right = "${tmpdir}/mid_surface_right.obj";

my @all_left_surfaces = ();
my @all_right_surfaces = ();

for ( my $i = 0;  $i < @surface_args;  $i += 3 ) {
  push @all_left_surfaces, $surface_args[$i + 1];
  push @all_right_surfaces, $surface_args[$i + 2];
}

`average_surfaces $mid_left none none 1 @all_left_surfaces`;
`average_surfaces $mid_right none none 1 @all_right_surfaces`;


################################################################################
# DRAW DATA VALUES OVER MID SURFACES
################################################################################

for ( my $i = 0;  $i < @data_args;  $i += 5 ) {
  my ($caption_text, $data_left, $data_right, $min, $max) = @data_args[$i .. $i + 4];

  # these two files get overwritten in the next iteration
  my $mid_rms_left = "${tmpdir}/${num_rows}_mid_rms_left.obj";
  my $mid_rms_right = "${tmpdir}/${num_rows}_mid_rms_right.obj";

  my $old_xpos = $xpos;
  $xpos = 0.85 * $xpos;
  $ypos += $tilesize;
  push( @DrawText, ( '-annotate', "0x0+${xpos}+${ypos}", $caption_text ) );
  $ypos += $tilesize;
  $xpos = $old_xpos;

  &run( 'colour_object', $mid_left, $data_left, $mid_rms_left, 'spectral', $min, $max);
  &run( 'colour_object', $mid_right, $data_right, $mid_rms_right, 'spectral', $min, $max);

  $num_rows += 1;
  foreach my $pos ('default', 'left', 'right') {
    my $tile_image = "${tmpdir}/${num_rows}_mid_left_$pos.rgb";
    make_hemi($mid_rms_left, $tile_image, $pos);
    push(@mont_args, $tile_image);
  }
  foreach my $pos ('top', 'bottom') {
    make_surface( $mid_rms_left, $mid_rms_right, "${tmpdir}/mid_${pos}.rgb", $pos );
    push(@mont_args, "${tmpdir}/mid_${pos}.rgb");
  }
  $num_rows += 1;
  foreach my $pos ('flipped', 'right', 'left') {
    my $tile_image = "${tmpdir}/${num_rows}_mid_right_$pos.rgb";
    make_hemi($mid_rms_right, $tile_image, $pos);
    push(@mont_args, $tile_image);
  }
  foreach my $pos ('front', 'back') {
    my $tile_image = "${tmpdir}/${num_rows}_mid_${pos}.rgb";
    make_surface( $mid_rms_left, $mid_rms_right, $tile_image, $pos );
    push(@mont_args, $tile_image);
  }
}

################################################################################
# FINISH UP BY RUNNING MONTAGE
################################################################################

# do the montage
&run( 'montage', '-tile', "5x${num_rows}", '-background', 'white',
      '-geometry', "${tilesize}x${tilesize}+1+1", @mont_args,
      "${tmpdir}/mont.png" );

# Add the title
&run( 'convert', '-box', 'white', '-stroke', 'green', '-pointsize', 16,
      @DrawText, "${tmpdir}/mont.png", ${output} );

# end of function

sub make_hemi {
  my ($surface, $temp_output, $pos) = @_;
  
  my @viewdir = ();
  if ($pos eq 'default') {
    push( @viewdir, qw( -view 0.77 -0.18 -0.6 0.55 0.6 0.55 ) );
  } else {
    if ($pos eq 'flipped') {
      push( @viewdir, qw( -view -0.77 -0.18 -0.6 -0.55 0.6 0.55 ) );
    } else {
      push( @viewdir, "-$pos" );
    }
  }

  &run( 'ray_trace', '-shadows', '-output', ${temp_output}, ${surface},
        '-bg', 'white', '-crop', @{viewdir} );
}

sub make_surface {
  my ($left_hemi, $right_hemi, $temp_output, $pos) = @_;
  
  my $viewdir = "";
  if ($pos eq 'default') {
    $viewdir = "";
  } else {
    $viewdir = "-$pos";
  }

  &run( 'ray_trace', '-shadows', '-output', ${temp_output}, ${left_hemi}, 
        ${right_hemi}, '-bg', 'white', '-crop', ${viewdir} );
}


#Execute a system call.

sub run {
  print "@_ \n";
  system(@_)==0 or die "Command @_ failed with status: $?";
}
