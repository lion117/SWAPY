# GUI object/properties browser. 
# Copyright (C) 2011 Matiychuk D.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
#    Free Software Foundation, Inc.,
#    59 Temple Place,
#    Suite 330,
#    Boston, MA 02111-1307 USA

#Boa:Frame:MainFrame

import const
import exceptions
import locale
import platform
import thread
import traceback
import wx

import code_manager
import proxy

#Avoid limit of wx.ListCtrl in 512 symbols
PROPERTIES = {}

def create(parent):
    return Frame1(parent)


[wxID_FRAME1, wxID_FRAME1LISTCTRL1_PROPERTIES, wxID_FRAME1STATICBOX_EDITOR, 
 wxID_FRAME1STATICBOX_OBJECTSBROWSER, wxID_FRAME1STATICBOX_PROPRTIES, 
 wxID_FRAME1TEXTCTRL_EDITOR, wxID_FRAME1TREECTRL_OBJECTSBROWSER
] = [wx.NewId() for _init_ctrls in range(7)]


class Frame1(wx.Frame):
    """
    Main application frame
    """
        
    def _init_ctrls(self, prnt):
    
        #-----Main frame-----
        wx.Frame.__init__(self, id=wxID_FRAME1, name='', parent=prnt, 
              style=wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER,
              title='SWAPY - Simple Windows Automation on Python v. %s. pywinauto v. %s. %s' % (const.VERSION,
                                                                                                proxy.pywinauto.__version__,
                                                                                                platform.architecture()[0]))
        self.SetIcon(wx.Icon(proxy.resource_path("swapy_dog_head.ico"),
              wx.BITMAP_TYPE_ICO))
              
        self.Bind(wx.EVT_MENU, self.menu_action) # - make action
        #----------
              
        #-----Static Boxes-----
        self.staticBox_ObjectsBrowser = wx.StaticBox(id=wxID_FRAME1STATICBOX_OBJECTSBROWSER,
              label='Objects browser', name='staticBox_ObjectsBrowser',
              parent=self)

        self.staticBox_Editor = wx.StaticBox(id=wxID_FRAME1STATICBOX_EDITOR,
              label='Editor', name='staticBox_Editor', parent=self,)
              
        self.staticBox_Proprties = wx.StaticBox(id=wxID_FRAME1STATICBOX_PROPRTIES,
              label='Properties', name='staticBox_Proprties', parent=self)
        #----------
              
        #-----ObjectsBrowser-----
        self.treeCtrl_ObjectsBrowser = wx.TreeCtrl(id=wxID_FRAME1TREECTRL_OBJECTSBROWSER,
              name='treeCtrl_ObjectsBrowser', parent=self, style=wx.TR_HAS_BUTTONS)
              
        self.treeCtrl_ObjectsBrowser.Bind(wx.EVT_TREE_SEL_CHANGED,
              self.ObjectsBrowserSelChanged, id=wxID_FRAME1TREECTRL_OBJECTSBROWSER)
              
        self.treeCtrl_ObjectsBrowser.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.ObjectsBrowserRightClick)
        #----------
        
        #-----Editor-----
        self.textCtrl_Editor = wx.TextCtrl(id=wxID_FRAME1TEXTCTRL_EDITOR,
              name='textCtrl_Editor', parent=self, style=wx.TE_MULTILINE | wx.TE_READONLY, value='')

        self.textCtrl_Editor.Bind(wx.EVT_CONTEXT_MENU, self.EditorContextMenu)
        
        self.textCtrl_Editor.SetInitialSize((300,250))
        #----------
        
        #-----Properties-----
        self.listCtrl_Properties = wx.ListCtrl(id=wxID_FRAME1LISTCTRL1_PROPERTIES, name='listCtrl1_Properties',
              parent=self, style=wx.LC_REPORT)
              
        self.listCtrl_Properties.InsertColumn(col=0, format=wx.LIST_FORMAT_LEFT,
              heading='Property', width=-1)
              
        self.listCtrl_Properties.InsertColumn(col=1, format=wx.LIST_FORMAT_LEFT,
              heading='Value', width=-1)
              
        self.listCtrl_Properties.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,
              self.PropertiesRightClick, id=wxID_FRAME1LISTCTRL1_PROPERTIES)
              
        #self.listCtrl_Properties.Bind(wx.EVT_LEFT_DCLICK, self.Refresh, id=wxID_FRAME1LISTCTRL1_PROPERTIES)
        #----------
        
        #-----Sizers-----
        staticBox_ObjectsBrowser_sizer = wx.StaticBoxSizer(self.staticBox_ObjectsBrowser)
        staticBox_ObjectsBrowser_sizer.Add(self.treeCtrl_ObjectsBrowser, 1, wx.EXPAND, 2)
        
        staticBox_Editor_sizer = wx.StaticBoxSizer(self.staticBox_Editor)
        staticBox_Editor_sizer.Add(self.textCtrl_Editor, 1, wx.EXPAND, 2)
        
        staticBox_Proprties_sizer = wx.StaticBoxSizer(self.staticBox_Proprties)
        staticBox_Proprties_sizer.Add(self.listCtrl_Properties, 1, wx.EXPAND, 2)
        
        sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        sizer_v = wx.BoxSizer(wx.VERTICAL)
                
        sizer_h.Add(staticBox_ObjectsBrowser_sizer, 1, wx.EXPAND, 2)
        sizer_h.Add(sizer_v, 1, wx.EXPAND|wx.ALL, 2)
        sizer_v.Add(staticBox_Editor_sizer, 1, wx.EXPAND, 2)
        sizer_v.Add(staticBox_Proprties_sizer, 1, wx.EXPAND, 2)
        
        self.SetSizerAndFit(sizer_h)
        #----------

    def __init__(self, parent):
        self._init_ctrls(parent)
        self._init_windows_tree()
        self.textCtrl_Editor.SetForegroundColour(wx.LIGHT_GREY)
        self.textCtrl_Editor.AppendText('#Perform an action - right click on item in the object browser.')
        self.prop_updater = prop_viewer_updater(self.listCtrl_Properties)
        self.tree_updater = tree_updater(self.treeCtrl_ObjectsBrowser)
        
    def ObjectsBrowserSelChanged(self, event):
        tree_item = event.GetItem()
        obj = self.treeCtrl_ObjectsBrowser.GetItemData(tree_item).GetData()
        if not obj._check_existence():
          self._init_windows_tree()
          tree_item = self.treeCtrl_ObjectsBrowser.GetRootItem()
          obj = self.treeCtrl_ObjectsBrowser.GetItemData(tree_item).GetData()
        self.prop_updater.props_update(obj)
        self.tree_updater.tree_update(tree_item, obj)
        obj.Highlight_control()
                    
    def ObjectsBrowserRightClick(self, event):
        menu = wx.Menu()
        #tree_item = self.treeCtrl_ObjectsBrowser.GetSelection()
        tree_item = event.GetItem()
        obj = self.treeCtrl_ObjectsBrowser.GetItemData(tree_item).GetData()
        self.GLOB_last_rclick_tree_obj = obj
        #self.treeCtrl_ObjectsBrowser.SelectItem(tree_item)
        if obj._check_existence():       
            actions = obj.Get_actions()
            extended_actions = obj.Get_extended_actions()
            if not actions and not extended_actions:
                menu.Append(0, 'No actions')
                menu.Enable(0, False)
            else:
                if extended_actions:
                    for _id, extended_action_name in extended_actions:
                        menu.Append(_id, extended_action_name)
                        if not obj._check_actionable():
                            menu.Enable(_id, False)
                    menu.AppendSeparator()

                for _id, action_name in actions:
                    menu.Append(_id, action_name)
                    if not obj._check_actionable():
                        menu.Enable(_id, False)

            self.PopupMenu(menu)
            menu.Destroy()
        else:
            self._init_windows_tree()
            tree_item = self.treeCtrl_ObjectsBrowser.GetRootItem()
            obj = self.treeCtrl_ObjectsBrowser.GetItemData(tree_item).GetData()
            self.prop_updater.props_update(obj)
            self.tree_updater.tree_update(tree_item, obj)
    
    def PropertiesRightClick(self, event):
        self.GLOB_prop_item_index = event.GetIndex()
        menu = wx.Menu()
        for _id, option_name in sorted(const.PROPERTIES_ACTIONS.items()):
            if option_name:
                menu.Append(_id, option_name)
            else:
                menu.AppendSeparator()
        self.PopupMenu(menu)
        menu.Destroy()

    def EditorContextMenu(self, event):
        cm = code_manager.CodeManager()
        menu = wx.Menu()

        for _id, option_name in sorted(const.EDITOR_ACTIONS.items()):
            if option_name:
                menu.Append(_id, option_name)
                if not cm:  # empty code
                    menu.Enable(_id, False)
            else:
                menu.AppendSeparator()
        if not self.textCtrl_Editor.GetStringSelection():  # empty selection
            menu.Enable(404, False)  # 404: 'Copy'

        self.PopupMenu(menu)
        menu.Destroy()

    def menu_action(self, event):
        menu_id = event.Id
        if menu_id in const.ACTIONS or \
                menu_id in const.EXTENDED_ACTIONS:
            # object browser menu
            # regular action or extended action
            self.make_action(menu_id)

        elif menu_id in const.PROPERTIES_ACTIONS:
            # properties viewer menu
            self.properties_action(menu_id)

        elif menu_id in const.EDITOR_ACTIONS:
            # editor menu
            self.editor_action(menu_id)

        else:
            raise RuntimeError("Unknown menu_id=%s for properties "
                               "menu" % menu_id)
    
    def properties_action(self, menu_id):
        item = self.GLOB_prop_item_index
        clipdata = wx.TextDataObject()

        if 'Copy all' == const.PROPERTIES_ACTIONS[menu_id]:
            all_texts = ''
            items_count = self.listCtrl_Properties.GetItemCount()
            for i in range(items_count):
                prop_name = self.listCtrl_Properties.GetItem(i, 0).GetText()
                val_name = self.listCtrl_Properties.GetItem(i, 1).GetText()
                all_texts += '%s : %s' % (prop_name, val_name) + '\n'
            clipdata.SetText(all_texts)

        elif 'Copy property' == const.PROPERTIES_ACTIONS[menu_id]:
            property = self.listCtrl_Properties.GetItem(item,0).GetText()
            clipdata.SetText(property)

        elif 'Copy value' == const.PROPERTIES_ACTIONS[menu_id]:
            #value = self.listCtrl_Properties.GetItem(item,1).GetText()
            key = self.listCtrl_Properties.GetItem(item,0).GetText()
            try:
                value_str = str(PROPERTIES[key])
            except exceptions.UnicodeEncodeError:
                value_str = PROPERTIES[key].encode(
                    locale.getpreferredencoding(), 'replace')
            clipdata.SetText(value_str)

        elif 'Copy unicode value' == const.PROPERTIES_ACTIONS[menu_id]:
            key = self.listCtrl_Properties.GetItem(item,0).GetText()
            try:
                value_unicode_escape = str(PROPERTIES[key])
            except exceptions.UnicodeEncodeError:
                value_unicode_escape = PROPERTIES[key].encode('unicode-escape',
                                                              'replace')
            clipdata.SetText(value_unicode_escape)
        else:
            raise RuntimeError("Unknown menu_id=%s for properties "
                               "menu" % menu_id)

        self.GLOB_prop_item_index = None
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

    def make_action(self, menu_id):
        obj = self.GLOB_last_rclick_tree_obj

        if menu_id in const.ACTIONS:
            # Regular action
            action = const.ACTIONS[menu_id]
            try:
                code = obj.Get_code(action)
                obj.Exec_action(action)
            except:
                code = None
                dlg = wx.MessageDialog(self, traceback.format_exc(5),
                                       'Warning!', wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()

        elif menu_id in const.EXTENDED_ACTIONS:
            # Extended action
            try:
                obj.SetCodestyle(menu_id)
                code = obj.Get_code()
            except:
                code = None
                dlg = wx.MessageDialog(self, traceback.format_exc(5),
                                       'Warning!', wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()

        if code is not None:
            self.textCtrl_Editor.SetForegroundColour(wx.BLACK)
            self.textCtrl_Editor.SetValue(code)

    def editor_action(self, menu_id):
        cm = code_manager.CodeManager()

        if 'Clear last command' == const.EDITOR_ACTIONS[menu_id]:
            cm.clear_last()
            self.textCtrl_Editor.SetValue(cm.get_full_code())

        elif 'Clear the code' == const.EDITOR_ACTIONS[menu_id]:
            def confirm_clearing():
                yes_no_dlg = wx.MessageDialog(self.textCtrl_Editor,
                                       "Are you sure you want to clear all of "
                                       "the code?",
                                       "Clear all?",
                                       wx.YES_NO | wx.ICON_QUESTION)
                result = yes_no_dlg.ShowModal() == wx.ID_YES
                yes_no_dlg.Destroy()
                return result

            if confirm_clearing():
                self.textCtrl_Editor.SetValue("")
                cm.clear()

        elif 'Copy' == const.EDITOR_ACTIONS[menu_id]:
            self.textCtrl_Editor.Copy()

        elif 'Select all' == const.EDITOR_ACTIONS[menu_id]:
            self.textCtrl_Editor.SetFocus()
            self.textCtrl_Editor.SelectAll()

        elif 'Save code to file' == const.EDITOR_ACTIONS[menu_id]:
            import os
            dlg = wx.FileDialog(self, "Choose a file", '', '', "*.py",
                                wx.SAVE | wx.OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                with open(os.path.join(dlg.GetDirectory(),
                                       dlg.GetFilename()), 'w') as out_file:
                    out_file.write("# automatically generated by SWAPY\n")
                    out_file.write(self.textCtrl_Editor.GetValue())
            dlg.Destroy()

        else:
            raise RuntimeError("Unknown menu_id=%s for editor "
                               "menu" % menu_id)

    def _init_windows_tree(self):
        self.treeCtrl_ObjectsBrowser.DeleteAllItems()
        item_data = wx.TreeItemData()
        root_obj = proxy.PC_system(None)
        item_data.SetData(root_obj)
        self.treeCtrl_ObjectsBrowser.AddRoot(root_obj.GetProperties()['PC name'], data = item_data)
        #self.treeCtrl_ObjectsBrowser.AddRoot('PC name')
        del item_data
        #the_root = self.treeCtrl_ObjectsBrowser.GetRootItem()
        #self.treeCtrl_ObjectsBrowser.Expand(self.treeCtrl_ObjectsBrowser.GetRootItem())


class prop_viewer_updater(object):
    def __init__(self, listctrl):
        self.listctrl = listctrl
        self.updating = False
        self.queue = []
        
    def props_update(self, obj):
        self.queue.append(obj)
        if self.updating:
            return 0 
        else:
            thread.start_new_thread(self._update,())
            
    def _update(self):
        self.updating = True
        obj = self.queue[-1]
        self.listctrl.DeleteAllItems()
        index = self.listctrl.InsertStringItem(0, 'Updating...')
        self.listctrl.SetStringItem(index, 1, '')
        global PROPERTIES
        try:
            PROPERTIES = obj.GetProperties()
        except:
            PROPERTIES = {}
            dlg = wx.MessageDialog(self.listctrl, traceback.format_exc(5),
                                   'Warning!', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        param_names = PROPERTIES.keys()
        param_names.sort(key=lambda name: name.lower(), reverse=True)
        
        if obj == self.queue[-1]:
            self.listctrl.DeleteAllItems()
            for p_name in param_names:
                p_name_str = str(p_name)
                try:
                    p_values_str = str(PROPERTIES[p_name])
                except exceptions.UnicodeEncodeError:
                    p_values_str = PROPERTIES[p_name].encode(
                        locale.getpreferredencoding(), 'replace')
                index = self.listctrl.InsertStringItem(0, p_name_str)
                self.listctrl.SetStringItem(index, 1, p_values_str)
            self.queue = []
            self.updating = False
        
        else:
            self._update()
            #there is the newer object for properties view.
            #Do not update listctrl
            #run _update again


class tree_updater(object):
    def __init__(self, treectrl):
        self.treectrl = treectrl
        self.updating = False
        self.queue = []
        
    def tree_update(self, tree_item, obj):
        self.queue.append((tree_item, obj))
        if self.updating:
            return 0 
        else:
            thread.start_new_thread(self._update,())
            
    def _update(self):
        self.updating = True
        tree_item, obj = self.queue[-1]
        self.treectrl.DeleteChildren(tree_item)
        subitems = obj.Get_subitems()
        for i_name, i_obj in subitems:
          item_data = wx.TreeItemData()
          item_data.SetData(i_obj)
          try:
              i_name_str = str(i_name)
          except exceptions.UnicodeEncodeError:
              i_name_str = i_name.encode(locale.getpreferredencoding(), 'replace')

          try:
            item_id = self.treectrl.AppendItem(tree_item, i_name_str, data=item_data)
            if (not i_obj._check_visibility()) or (not i_obj._check_actionable()):
                self.treectrl.SetItemTextColour(item_id,'gray')
          except wx._core.PyAssertionError:
              pass
              #Ignore tree item creation error when parent is not exists
          finally:
              del item_data
        self.treectrl.Expand(self.treectrl.GetRootItem())
        
        if (tree_item, obj) == self.queue[-1]:
          self.queue = []
          self.updating = False
        
        else:
            self._update()
            #there is the newer object for tree view.
            #Do not update treeCtrl
            #run _update again