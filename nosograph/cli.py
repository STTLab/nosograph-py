import dotenv
import os
from time import sleep
from datetime import datetime
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
import nosograph._txs as txs
from nosograph.db import NosoGraph
from nosograph.models.specimen import Sample
from nosograph.pipeline import NosoGraphPipeline
from nosograph.types import Neo4JAuth

dotenv.load_dotenv('.env')
NEO4J_URI = os.environ.get(
    'NEO4J_URI',
    f'neo4j://{os.environ.get("NEO4J_HOST", "localhost")}:{os.environ.get("NEO4J_BOLT_PORT", "7687")}'
)
NEO4J_AUTH = Neo4JAuth.from_string(os.environ.get('NEO4J_AUTH', None))


class NosoGraphCLI:
    def __init__(self):
        self._window_size = 40
        self.SEX_MAP = {1: 'M', 2: 'F', 3: None}
        self.neo4j_conn = NosoGraph(NEO4J_URI, NEO4J_AUTH)
        self.neo4j_conn.verify()

    def _ui_element_hbar(self, char: str = '-', width: int | None = None):
        if width:
            return char * width
        return char * self._window_size

    def selection_menu(self, title: str, options: list, default: int | None = None, retry: bool = False):
        if not retry:
            if title != '':
                print(self._ui_element_hbar())
                print(title)
                print(self._ui_element_hbar())
            for i, option in enumerate(options):
                print(f'{i + 1}) {option}')
        print('')
        if default:
            select = input(f'Select option [{default}]: ')
            if select == '':
                return default
        else:
            select = input('Select option: ')
        try:
            select = int(select)
            if select < 1 or select > len(options):
                raise ValueError('No such option')
            return int(select)
        except ValueError as e:
            print(f'Invalid input: {e}')
            return self.selection_menu(title, options, default, retry=True)

    def main_menu(self):
        while True:
            select = self.selection_menu('NosoGraph CLI', ['Patients', 'Samples', 'Assembly pipeline', 'Exit'])
            match select:
                case 1:
                    self.patient_menu()
                case 2:
                    self.sample_menu()
                case 3:
                    self.assembly_pipeline_menu()
                case 4:
                    exit(0)

    def patient_menu(self):
        select = self.selection_menu('Patients', ['Create Patient', 'Get Patient', 'load CSV', '<-- Back'])
        match select:
            case 1:
                self.create_patient()
            case 2:
                print('')
                patient_id = input('Patient ID: ')
                patient = self.get_patient(patient_id)
                self.print_patient_info(patient)
            case 3:
                pass
            case 4:
                return

    def print_patient_info(self, patient_info):
        if not patient_info:
            print('Not found\n')
            sleep(1)
            return
        print(f'Firstname: {patient_info.get("firstname")}')
        print(f'Lastname: {patient_info.get("lastname")}')
        print(f'Sex: {patient_info.get("sex")}')
        print(f'Date of Birth: {patient_info.get("date_of_birth")}')
        print(f'Age: {patient_info.get("age")}\n')
        sleep(3)

    def create_patient(self):
        patient_id = input('Patient ID/HN: ').strip()
        with self.neo4j_conn.driver.session() as session:
            count = session.execute_read(
                lambda tx: tx.run(
                    'MATCH (p:Patient) WHERE p.patient_id = $patient_id RETURN COUNT(p) AS count',
                    patient_id=patient_id
                ).single()["count"]
            )
            if count > 0:
                raise ValueError(f"Patient with ID '{patient_id}' already exists")
            firstname = input('Firstname: ').strip()
            lastname = input('Lastname: ').strip()
            print('\nSex')
            sex = self.SEX_MAP.get(self.selection_menu('', ['Male', 'Female', 'Unknown'], 3))
            print('Date of birth (YYYY-MM-DD) - Blank if unknown to input age')
            date_of_birth = input('> ').strip()
            dob_value = None
            age_value = None
            if date_of_birth == '':
                age_input = input('Age: ').strip()
                if age_input:
                    try:
                        age_value = int(age_input)
                    except ValueError:
                        raise ValueError("Age must be a number")
            else:
                try:
                    datetime.strptime(date_of_birth, "%Y-%m-%d")
                    dob_value = date_of_birth
                except ValueError:
                    raise ValueError("Invalid date format. Use YYYY-MM-DD")
            session.execute_write(txs._create_patient_tx, patient_id, firstname, lastname, sex, dob_value, age_value)
            self.neo4j_conn._logger.info(f"Created patient {patient_id}")
            print("Patient created successfully")

    def get_patient(self, patient_id):
        with self.neo4j_conn.driver.session() as session:
            return session.execute_read(txs._get_patient_by_id, patient_id)

    def load_csv(self):
        pass

    def sample_menu(self):
        select = self.selection_menu('Samples', ['Create Sample', 'Get Sample', 'load CSV', '<-- Back'])
        match select:
            case 1:
                self.create_sample()
            case 2:
                print('')
                sample_id = input('Sample ID: ')
                sample = self.get_sample(sample_id)
                self.print_sample_info(sample)
            case 3:
                pass
            case 4:
                return

    def create_sample(self):
        sample_id = input('Sample ID: ').strip()
        if not sample_id:
            raise ValueError("Sample ID cannot be empty")
        if self.neo4j_conn.samples.get(sample_id) is not None:
            raise ValueError(f"Sample with ID '{sample_id}' already exists")
        self.neo4j_conn.samples.create(Sample(sample_id=sample_id))
        self.neo4j_conn._logger.info(f"Created sample {sample_id}")
        print("Sample created successfully")

    def get_sample(self, sample_id):
        return self.neo4j_conn.samples.get(sample_id)

    def print_sample_info(self, sample_info):
        if not sample_info:
            print('Not found\n')
            sleep(1)
            return
        print(f'Sample ID: {sample_info.sample_id}')
        variants = self.neo4j_conn.variants.get_by_sample(sample_info.sample_id)
        print(f'Linked variants: {len(variants)}\n')
        sleep(2)

    def assembly_pipeline_menu(self):
        select = self.selection_menu('Assembly Pipeline', ['Run pipeline', 'Upload data to knowledge graph', '<-- Back'])
        match select:
            case 1:
                self.pipeline_prompt()
            case 2:
                print('')
                sample_id = input('Sample ID: ')
                sample = self.get_sample(sample_id)
                self.print_sample_info(sample)
            case 3:
                return

    def pipeline_prompt(self):
        def _path(label: str) -> str:
            print(label)
            return prompt('> ', completer=PathCompleter()).strip()

        script_path = _path('Path to assembly pipeline script (nosograph_pipeline.sh)')
        long_reads = _path('Path to Long reads FASTQ (gzipped or not)')
        short_r1 = _path('Path to Short reads R1 FASTQ')
        short_r2 = _path('Path to Short reads R2 FASTQ')

        assembler = ['flye', 'canu'][self.selection_menu('Assembler', ['flye', 'canu']) - 1]
        technology = ['nanopore', 'pacbio'][self.selection_menu('Sequencing technology', ['nanopore', 'pacbio']) - 1]

        genome_size = None
        if assembler == 'canu':
            genome_size = input('Genome size (e.g. 5m) [required for canu]: ').strip() or None

        outdir = _path('Output directory')
        threads_input = input('Threads [1]: ').strip()
        threads = int(threads_input) if threads_input else 1

        pipeline = NosoGraphPipeline(
            script_path=script_path,
            long_reads=long_reads,
            short_r1=short_r1,
            short_r2=short_r2,
            assembler=assembler,
            technology=technology,
            outdir=outdir,
            genome_size=genome_size,
            threads=threads,
        )
        print('Running pipeline...')
        pipeline.run()
        print('Pipeline finished')


if __name__ == '__main__':
    cli = NosoGraphCLI()
    cli.main_menu()
