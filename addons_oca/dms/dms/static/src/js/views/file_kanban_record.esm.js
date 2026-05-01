// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {KanbanRecord} from "@web/views/kanban/kanban_record";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";

const videoReadableTypes = ["x-matroska", "mp4", "webm"];
const audioReadableTypes = ["mp3", "ogg", "wav", "aac", "mpa", "flac", "m4a"];

export class FileKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.store = useService("mail.store");
        this.fileViewer = useFileViewer();
        this.action = useService("action");
    }

    isVideo(mimetype) {
        return videoReadableTypes.includes(mimetype);
    }

    isAudio(mimetype) {
        return audioReadableTypes.includes(mimetype);
    }

    /**
     * @override
     *
     * Override to open the preview upon clicking the image, if compatible.
     */
    onGlobalClick(ev) {
        const self = this;

        if (ev.target.closest(".oe_kanban_global_click")) {
            const file_type = self.props.record.data.name.split(".")[1];
            let mimetype = "";

            if (self.isVideo(file_type)) {
                mimetype = `video/${file_type}`;
            } else if (self.isAudio(file_type)) {
                mimetype = "audio/mpeg";
            } else {
                mimetype = self.props.record.data.mimetype;
            }

            const attachmentData = {
                id: self.props.record.data.id,
                filename: self.props.record.data.name,
                name: self.props.record.data.name,
                mimetype: mimetype,
                model_name: self.props.record.resModel,
                displayName: self.props.record.data.name,
                defaultSource: `/web/content?id=${self.props.record.data.id}&field=content&model=dms.file&filename_field=name`,
            };
            
            const openWithAction = () => {
                this.action.doAction({
                    type: 'ir.actions.act_url',
                    url: attachmentData.defaultSource,
                    target: 'new',
                });
            };

            try {
                const AttachmentModel = this.store?.Attachment || this.store?.models?.Attachment;
                if (AttachmentModel && typeof AttachmentModel.insert === 'function') {
                    const attachment = AttachmentModel.insert(attachmentData);
                    this.fileViewer.open(attachment);
                } else {
                    openWithAction();
                }
            } catch (e) {
                openWithAction();
            }
            return;
        }
        
        // If clicking anywhere else on the card, also try to preview if it's a file
        if (ev.target.closest(".oe_kanban_global_click")) {
             // Fallback to open the form or preview
             // For now, let's keep it standard but if they want the whole card to preview, we can change this.
        }

        return super.onGlobalClick(ev);
    }
}
