#!/usr/env/python3
import os
import json

cubit.cmd('reset')

def find_number_of_volumes_in_each_step_file(input_locations):
    body_ids=''
    volumes_in_each_step_file=[]
    starting_group_id = 5
    for entry in input_locations:
      current_vols =cubit.parse_cubit_list("volume", "all")
      print(entry['filename'])
      cubit.cmd('import step "' + entry['filename'] + '" separate_bodies no_surfaces no_curves no_vertices heal group "'+str(entry['filename'])+'"')
      all_vols =cubit.parse_cubit_list("volume", "all")
      new_vols = set(current_vols).symmetric_difference(set(all_vols))
      new_vols = map(str, new_vols)
      print('new_vols',new_vols,type(new_vols))
      volumes_in_group = cubit.cmd('volume in group '+str(starting_group_id))
      print('volumes_in_group',volumes_in_group,type(volumes_in_group))
      cubit.cmd('unite vol '+ ' '.join(new_vols))
      new_vols_after_unite = set(current_vols).symmetric_difference(set(all_vols))
      new_vols_after_unite = map(str, new_vols_after_unite)      
      #cubit.cmd('group '+str(starting_group_id)+' copy rotate 45 about z repeat 7')
      entry['volumes']=new_vols_after_unite
      #cubit.cmd('volume in group '+str(starting_group_id)+' copy rotate 45 about z repeat 7')
      starting_group_id = starting_group_id +1
    return input_locations

def create_graveyard():
  cubit.cmd('brick x 110')
  cubit.cmd('brick x 111')
  cubit.cmd('subtract volume 1 from volume 2')
  cubit.cmd('group "mat:Graveyard" add volume 3')
  cubit.cmd('volume 3 visibility off')

def load_reflecting_wedge(input_location_wedge):
  current_vols =cubit.parse_cubit_list("volume", "all")  
  cubit.cmd('import step "' + input_location_wedge + '" heal')
  all_vols =cubit.parse_cubit_list("volume", "all")
  new_vols = set(current_vols).symmetric_difference(set(all_vols))
  new_vols = map(str, new_vols)  
  surfaces_in_volume = cubit.parse_cubit_list("surface", " in volume "+' '.join(new_vols))
  print(surfaces_in_volume)
  surface_info_dict = {}
  for surface_id in surfaces_in_volume:
    surface = cubit.surface(surface_id)
    #area = surface.area()
    vertex_in_surface = cubit.parse_cubit_list("vertex", " in surface " + str(surface_id))
    if surface.is_planar()==True and len(vertex_in_surface) == 4 :
      surface_info_dict[surface_id] = {'reflector':True}
    else:
      surface_info_dict[surface_id] = {'reflector':False}
    print()
  print('surface_info_dict',surface_info_dict)
  cubit.cmd('group "mat:Vacuum" add volume '+ ' '.join(new_vols))
  cubit.cmd('volume '+' '.join(new_vols)+' visibility off')
  return surface_info_dict

def load_common_wedge(input_location_wedge):
  current_vols =cubit.parse_cubit_list("volume", "all")
  cubit.cmd('import step "' + input_location_wedge + '" no_surfaces no_curves no_vertices heal group common_wedge')
  all_vols =cubit.parse_cubit_list("volume", "all")
  new_vols = set(current_vols).symmetric_difference(set(all_vols))
  new_vols = map(str, new_vols)
  cubit.cmd('volume '+' '.join(new_vols)+' visibility off')
  return new_vols  

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def find_reflecting_surfaces(surface_info_dict):
    surfaces_in_wedge_volume = cubit.parse_cubit_list("surface", " in volume 4")
    for surface_id in surface_info_dict.keys():
        if surface_info_dict[surface_id]['reflector']==True:
            print(surface_id, 'surface originally reflecting but does it still exist')
            if surface_id not in surfaces_in_wedge_volume:
                del surface_info_dict[surface_id]
    for surface_id in surfaces_in_wedge_volume:
        if surface_id not in surface_info_dict.keys():
            surface_info_dict[surface_id]= {'reflector':True}
    return surface_info_dict

# os.system('python3 make_materials.py')
create_graveyard()
wedge_surface_info_dict = load_reflecting_wedge(input_location_wedge="reflecting_wedge.stp")
#common_wedge_volume = load_common_wedge(input_location_wedge="common_wedge.stp")


with open('model_description.json') as f:
    geometry_details = byteify(json.load(f))



geometry_details = find_number_of_volumes_in_each_step_file(geometry_details)

print('geometry_details',geometry_details)

for entry in geometry_details:
   cubit.cmd('group "mat:'+entry['material']+'" add volume ' +' '.join(entry['volumes']))
   #cubit.cmd('unite vol '+ ' '.join(entry['volumes']))
   print(entry)
   if "color" in entry.keys():
    print('color in keys')
    # Available Colors https://www.csimsoft.com/help/appendix/available_colors.htm
    cubit.cmd('Color volume '+' '.join(entry['volumes'])+ ' '+ entry['color'])

#volume in group 12 copy rotate 45 about z repeat 7


cubit.cmd('vol all scale 100')
cubit.cmd('imprint body all')
#cubit.cmd('merge tolerance 1.e-4')
cubit.cmd('merge vol all group_results tolerance 1.e-4')
cubit.cmd('graphics tol angle 3')

updated_wedge_surface_info_dict = find_reflecting_surfaces(wedge_surface_info_dict)
print('wedge_surface_info_dict',wedge_surface_info_dict)

for surface_id in updated_wedge_surface_info_dict.keys():
  if updated_wedge_surface_info_dict[surface_id]['reflector'] == True:
    cubit.cmd('group "boundary:Reflecting" add surf ' +str(surface_id))
    cubit.cmd('surface ' +str(surface_id)+' visibility on')


cubit.cmd('set attribute on')
#cubit.cmd('export dagmc "geometry_and_materials.h5m" faceting_tolerance 1.0e-4')

cubit.cmd('export dagmc "geometry_with_material_tags.h5m" faceting_tolerance 1.0e-2')



#cubit.cmd('delete mesh')
#cubit.cmd('delete volume 3 4')
#cubit.cmd('Trimesher volume gradation 1.3')
#cubit.cmd('volume all size auto factor 5')
#cubit.cmd('mesh volume all')

# additional steps needed for unstructured mesh https://svalinn.github.io/DAGMC/usersguide/tally.html
os.system('rm *.jou')