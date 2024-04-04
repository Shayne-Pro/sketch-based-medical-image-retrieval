import os
import vtk
import json
import glob
import numpy as np
import scipy.misc
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox

from database import DatabaseManager
from database import User
from database import ResultSummary
from database.db_models import BraTSImage

from .feature_extractor import FeatureExtractor
from .widget import MainWindow
from .widget.contour_module.rasterise import make_masked_image
from .widget.contour_module.structure import Structure
from .widget.utils.state import StateBase
from .dialog import ModalityDialog
from .widget.utils import font
from .widget.utils import font_semibold


NOT_STARTED = 'NOT_STARTED'
STAGE_1 = 'STAGE_1'
STAGE_2 = 'STAGE_2'
STAGE_3 = 'STAGE_3'
FINAL = 'FINAL'

MAX_PAGES_PER_STAGE = 10
BRUSH = 'BRUSH'
LINE = 'LINE'

TOPK_IMAGE = 200
TOPK_PATIENT = 10
DPI = 512

MICCAI_BraTS = 'MICCAI_BraTS'


def save_as_image(image, path, cmap, vmin=None, vmax=None):
    if vmin is None:
        vmin = image.min()

    if vmax is None:
        vmax = image.max()

    plt.axis('off')
    plt.imshow(image, cmap=cmap, vmin=vmin, vmax=vmax)
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=DPI)
    plt.clf()


class AppController(object):

    def __init__(self, mode, config, dataset_type, dataset_name, model_name):
        super().__init__()

        self.mode = mode
        self.user_model = None

        self.gl_config = config
        self.ds_config = config['dataset_types'][dataset_type]

        self.app_state = StateBase(
            user='Test',
            y_experience=0,
            dataset_type=dataset_type,
            dataset_name=dataset_name,
            model_name=model_name,
            stage=1,
            question=1,
            structure_list=[],
            structure_idx=0,
            current_template_image=None,
            current_sketch_image=None,
        )

        self.init()

    def init(self):
        self.MainWidget = MainWindow(self.mode, self)

        self.QueryWidget.init_viewer(
            image_path=self.ds_config['template']['nifti_path'],
            window_width=self.ds_config['viewer']['ct_window']['window_width'],
            window_center=self.ds_config['viewer']['ct_window']['window_center'],
        )
        self.init_structure_list()
        self.QueryWidget.start_viewer()

        self.module_progress = QProgressDialog(
            'Now starting ...', None, 0, 0, parent=self.MainWidget)
        self.module_progress.setWindowTitle(' ')
        self.module_progress.setFont(font)
        self.module_progress.setModal(True)
        self.module_progress.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.CustomizeWindowHint)
        self.module_progress.show()

        self.worker = StartModuleWorker(self)
        self.worker.finished.connect(self._start_app)
        self.worker.start()

    def _start_app(self, signal):
        self.module_progress.close()
        self.DatabaseManager = signal['DatabaseManager']
        self.FeatureExtractor = signal['FeatureExtractor']

        if self.mode == 'testing':
            self.MainWidget.edit_user_information(freeze=False)

            self.user_model = User.create_record(
                user_name=self.app_state['user'],
                y_experience=self.app_state['y_experience'],
            )

    def init_modules(self):
        model_name = self.app_state['model_name']
        database_manager = DatabaseManager(
            project_name=self.gl_config['mongodb']['project_name'],
            dataset_name=self.app_state['dataset_name'],
            annoy_model_path=self.gl_config['annoy']['annoy_model_path'],
            slice_root_dir_path=self.gl_config['mongodb']['slice_root_dir_path'],
            nifti_root_dir_path=self.gl_config['mongodb']['nifti_root_dir_path'],
            code_root_dir_path=self.gl_config['mongodb']['code_root_dir_path'],
            model_name=self.app_state['model_name'],
            n_trees=self.gl_config['annoy']['n_trees'],
            vector_length=self.ds_config['models'][model_name]['vector_length'],
            alias=self.gl_config['mongodb']['alias'],
            host=self.gl_config['mongodb']['host']
        )

        network_config = self.ds_config['models'][model_name]['network_config']
        saved_model_path = self.ds_config['models'][model_name]['saved_model_path']

        feature_extractor = FeatureExtractor(
            network_config=network_config,
            saved_model_path=saved_model_path,
        )

        return database_manager, feature_extractor

    def register_widget(self, widget, key):
        if key == 'main':
            self.MainWidget = widget

        elif key == 'query':
            self.QueryWidget = widget

        elif key == 'nav':
            self.QuestionWidget = widget

        elif key == 'result':
            self.ResultWidget = widget

            ww = self.ds_config['viewer']['ct_window']['window_width']
            wc = self.ds_config['viewer']['ct_window']['window_center']

            vmin = wc - ww // 2
            vmax = wc + ww // 2

            self.ResultWidget.set_ct_window(vmin, vmax)

    def init_structure_list(self):
        get_color = vtk.vtkNamedColors().GetColor3d

        structure_list = []
        for temp_structure in self.ds_config['structure']['structure_list']:
            structure_list.append(
                Structure(temp_structure['class_name'],
                          temp_structure['name'],
                          get_color(temp_structure['color']),
                          self.QueryWidget.viewer_controller.state)
            )

        self.app_state['structure_list'] = structure_list

    def normalize_ct_image(self, image, width, center, scale):
        vmax = center + width // 2
        vmin = center - width // 2

        image = np.clip(image, a_min=vmin, a_max=vmax)
        image -= vmin
        image /= (vmax - vmin)
        image -= 0.5
        image *= scale

        return image

    def get_template_image(self):
        current_slice = self.QueryWidget.viewer_controller.state['slice']
        max_slice = self.QueryWidget.get_z_length() - 1
        slice_num = max_slice - current_slice

        if self.app_state['dataset_type'] == MICCAI_BraTS:
            series = []
            for modality in self.ds_config['template']['modalities']:
                patient_id = self.ds_config['template']['patient_id']
                template_slice_root_path = self.ds_config['template']['slice_root_dir_path']

                file_path = os.path.join(
                    template_slice_root_path,
                    patient_id,
                    patient_id +
                    '_{}_{}.npy'.format(modality, str(slice_num).zfill(4)),
                )

                series.append(
                    np.load(file_path).astype(np.float32)[np.newaxis, ...]
                )

            template_image = np.concatenate(series, axis=0)

        else:
            raise NotImplementedError(
                'Only the MICCAI BraTS 2019 dataset is available in the public version.')

        return template_image

    def concat_masked_image(self, masked_images):
        sketch_image = None
        for structure_name in self.ds_config['structure']['order']:
            class_id = masked_images[structure_name]['class_id']
            structure_mask = masked_images[structure_name]['structure_mask']

            if sketch_image is None:
                sketch_image = structure_mask
            else:
                sketch_image[structure_mask == class_id] = class_id

        return sketch_image

    def extract_query_vector(self):
        current_slice = self.QueryWidget.viewer_controller.state['slice']
        template_image = self.get_template_image()

        extent = self.QueryWidget.get_axial_extent()
        origin = self.QueryWidget.get_image_origin()
        spacing = self.QueryWidget.get_image_spacing()
        structure_list = self.app_state['structure_list']

        class_name_to_id = self.ds_config['structure']['class_name_to_id']

        masked_images = {}
        for structure in structure_list:
            assert len(structure.contours.keys()) < 2

            contours = structure.contours[current_slice]
            structure_mask = np.zeros(extent)
            class_id = class_name_to_id[structure.class_name]

            for contour_idx in contours:
                points = contours[contour_idx]['points']

                if points is not None:
                    _masked_image = make_masked_image([points],
                                                      np.zeros(extent),
                                                      1,
                                                      extent[0],
                                                      extent[1],
                                                      origin,
                                                      spacing,
                                                      )

                    structure_mask[_masked_image == 1] = 1

            structure_mask = scipy.misc.imresize(
                structure_mask.astype(np.uint8),
                (template_image[0].shape[0], template_image[0].shape[1]),
                interp='nearest',
                mode='L',
            )

            structure_mask *= class_id

            masked_images[structure.class_name] = {
                'class_id': class_id,
                'structure_mask': structure_mask,
            }

        sketch_image = self.concat_masked_image(masked_images)

        q_eac, q_nac, q_aac = self.FeatureExtractor.extract_feature(
            template_image, sketch_image)

        return q_eac, q_nac, q_aac, template_image, sketch_image

    def filter_by_patient(self, results):
        patient_ids = []
        extracted_results = []

        for result in results:
            if not result.patient_id in patient_ids:
                patient_ids.append(result.patient_id)
                extracted_results.append(result)

        extracted_results = extracted_results[:TOPK_PATIENT]

        return extracted_results

    def get_image(self, patient_id, slice_num):
        images = []

        for modality in self.ds_config['reference']['modalities']:
            file_name = patient_id + '_' + modality + \
                '_' + str(slice_num).zfill(4) + '.npy'
            image_path = os.path.join(
                self.ds_config['reference']['slice_root_dir_path'], patient_id, file_name)

            image = np.load(image_path)

            images.append({
                'patient_id': patient_id,
                'slice_num': slice_num,
                'modality': modality,
                'image': image,
            })

        return images

    def search_images(self):
        # font = QFont()
        # font.setFamily("Segoe UI")

        self.search_progress = QProgressDialog(
            'Now searching ...', None, 0, 0, parent=self.MainWidget)
        self.search_progress.setWindowTitle(' ')
        self.search_progress.setFont(font)
        self.search_progress.setModal(True)
        self.search_progress.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.CustomizeWindowHint)
        self.search_progress.show()

        self.worker = SearchImageWorker(self)
        self.worker.finished.connect(self._show_results)
        self.worker.start()

    def _show_results(self, payload):
        self.app_state['current_template_image'] = payload['template_image']
        self.app_state['current_sketch_image'] = payload['sketch_image']
        retrieved_images = payload['retrieved_images']
        retrieved_records = payload['retrieved_records']

        self.search_progress.close()
        self.ResultWidget.show_results(retrieved_images, retrieved_records)

    def next_page(self, result_summary):
        self.QueryWidget.stop_sketching()
        self.ResultWidget.clear()

        matched_retrieved_num = -1
        if self.QuestionWidget.config['type'] == 'image':
            question_patient_id = self.QuestionWidget.config['patient_id']

            is_matched = False
            for i, result in enumerate(result_summary):
                retrieved_patient_id = result['patient_id']

                if question_patient_id == retrieved_patient_id:
                    is_matched = True
                    matched_retrieved_num = i

                    QMessageBox.information(
                        self.MainWidget,
                        'Retrieval succeeded',
                        'The retrieved case #{} is the same with the presented case.'.format(
                            i + 1),
                        QMessageBox.Yes,
                    )

            if not is_matched:
                QMessageBox.information(
                    self.MainWidget,
                    'Retrieval failed',
                    'The presented case was not retrieved in top-{}.'.format(
                        TOPK_PATIENT),
                    QMessageBox.Yes,
                )

        created_at = (self.user_model.created_at).strftime("%m-%d-%Y-%H-%M-%S")
        user_name = self.user_model.user_name
        y_experience = self.user_model.y_experience

        user_unique_key = user_name + '_yexp_' + \
            str(y_experience) + '_' + created_at

        stage_num = self.app_state['stage']
        question_num = self.app_state['question']

        # save template and sketch images
        save_dir_path = os.path.join(
            self.gl_config['save']['save_result_path'],
            self.app_state['dataset_type'],
            user_unique_key,
            'stage_num_{}'.format(stage_num),
            'question_num_{}'.format(question_num),
        )

        os.makedirs(save_dir_path, exist_ok=True)

        np.save(
            os.path.join(save_dir_path, 'template_image.npy'),
            self.app_state['current_template_image'],
        )

        save_as_image(
            self.app_state['current_template_image'][0, ...],
            os.path.join(save_dir_path, 'template_image.png'),
            cmap='gray',
        )

        np.save(
            os.path.join(save_dir_path, 'sketch_image.npy'),
            self.app_state['current_sketch_image'],
        )

        save_as_image(
            self.app_state['current_sketch_image'],
            os.path.join(save_dir_path, 'sketch_image.png'),
            cmap='jet', vmin=0, vmax=3,
        )

        # save result summary as json
        result_json = {
            'created_at': created_at,
            'user_name': user_name,
            'y_experience': y_experience,
            'stage_num': stage_num,
            'question_num': question_num,
            'matched_retrieved_num': matched_retrieved_num,
            'result_summary': result_summary,
        }

        with open(os.path.join(save_dir_path, 'result.json'), 'w') as f:
            json.dump(result_json, f, indent=2)

        # save result summary in the mongodb
        result_summary_model = ResultSummary.save_summary(
            user_unique_key=user_unique_key,
            user_record=self.user_model,
            stage_num=stage_num,
            question_num=question_num,
            template_image_path=os.path.join(
                save_dir_path, 'template_image.npy'),
            sketch_image_path=os.path.join(save_dir_path, 'sketch_image.npy'),
            matched_retrieved_num=matched_retrieved_num,
            result_summary=result_summary,
        )

        next = self.QuestionWidget.next()

        if next is False:
            QMessageBox.information(
                self.MainWidget,
                'INFORMATION', 'The test is finished.',
                QMessageBox.Yes,
            )

    def show_image_in_viewer(self, record):
        if self.app_state['dataset_type'] == MICCAI_BraTS:
            modality_dialog = ModalityDialog(self.ds_config)

            if modality_dialog.exec_() == QDialog.Accepted:
                selected_modality = modality_dialog.modalityComboBox.currentText().lower()
            else:
                selected_modality = None

        else:
            raise NotImplementedError(
                'Only the MICCAI BraTS 2019 dataset is available in the public version.')

        if selected_modality:
            if isinstance(record, (BraTSImage)):
                patient_id = record.patient_id
                selected_slice = record.slice_num
                nifti_path = record.get_nifti_image_path(
                    modality=selected_modality)

                viewer_title = 'Retrieved image - {} - {}'.format(
                    patient_id, selected_modality.upper()
                )

            else:
                patient_id = record['patient_id']
                selected_slice = record['selected_slice']

                if self.app_state['dataset_type'] == MICCAI_BraTS:
                    file_name = patient_id + '_' + selected_modality + '.nii.gz'
                    nifti_path = os.path.join(
                        self.config['reference']['nifti_root_dir_path'],
                        patient_id,
                        file_name,
                    )

                    viewer_title = 'Question - Brain MRI - {}'.format(
                        selected_modality.upper())

                else:
                    raise NotImplementedError(
                        'Only the MICCAI BraTS 2019 dataset is available in the public version.')

            self.MainWidget.run_viewer(
                patient_id=patient_id,
                image_path=nifti_path,
                window_width=self.ds_config['viewer']['ct_window']['window_width'],
                window_center=self.ds_config['viewer']['ct_window']['window_center'],
                viewer_title=viewer_title,
                selected_slice=selected_slice,
            )


class StartModuleWorker(QThread):

    finished = pyqtSignal(object)

    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller

    def run(self):
        database_manager, feature_extractor = self.app_controller.init_modules()
        self.finished.emit({
            'DatabaseManager': database_manager,
            'FeatureExtractor': feature_extractor,
        })


class SearchImageWorker(QThread):

    finished = pyqtSignal(object)

    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller

    def run(self):
        q_eac, q_nac, q_aac, template_image, sketch_image = self.app_controller.extract_query_vector()

        results = self.app_controller.DatabaseManager.query(
            q_eac, topk=TOPK_IMAGE)
        records = self.app_controller.filter_by_patient(results)

        retrieved_images = []
        for record in records:
            retrieved_image = self.app_controller.get_image(
                record.patient_id, record.slice_num
            )
            retrieved_images.append(retrieved_image)

        payload = {
            'template_image': template_image,
            'sketch_image': sketch_image,
            'retrieved_images': retrieved_images,
            'retrieved_records': records,
        }

        self.finished.emit(payload)
